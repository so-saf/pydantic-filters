import pytest
import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic_filters import BaseFilter, SearchField, SearchType
from pydantic_filters.drivers.sqlalchemy._exceptions import (
    AttributeNotFoundSaDriverError,
    RelationshipNotFoundSaDriverError,
)
from pydantic_filters.drivers.sqlalchemy._mapping import (
    filter_to_column_clauses,
    filter_to_join_targets,
    JoinParams,
)


class Base(so.DeclarativeBase):
    pass


class CModel(Base):
    __tablename__ = "c"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    a_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("a.id"))


class BModel(Base):
    __tablename__ = "b"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    
    
BModelAliased: so.util.AliasedClass = so.aliased(BModel)  # type: ignore


class LeafModel(Base):
    __tablename__ = "leaf"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)


class MiddleModel(Base):
    __tablename__ = "middle"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    leaf_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(LeafModel.id))
    leaf: so.Mapped[LeafModel] = so.relationship()


class RootModel(Base):
    __tablename__ = "root"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    middle_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(MiddleModel.id))
    middle: so.Mapped[MiddleModel] = so.relationship()


class ArrayModel(Base):
    __tablename__ = "array_model"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    tags: so.Mapped[list[str]] = so.mapped_column(sa.ARRAY(sa.String))


class NodeModel(Base):
    __tablename__ = "node"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    parent_id: so.Mapped[int | None] = so.mapped_column(sa.ForeignKey("node.id"))
    parent: so.Mapped["NodeModel | None"] = so.relationship(remote_side="NodeModel.id")


class AModel(Base):
    __tablename__ = 'a'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str]
    b_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(BModel.id))
    b: so.Mapped[BModel] = so.relationship()
    c: so.Mapped[list[CModel]] = so.relationship()


class CFilter(BaseFilter):
    id: int


class BFilter(BaseFilter):
    id: int


class FilterTest(BaseFilter):
    id: int
    id__lt: int
    name: str
    name__null: bool
    name__n: list[str]
    biba: str

    q1: str = SearchField(target=["name"])
    q1_2: str = SearchField(target=["id", "name"])
    q2: list[str] = SearchField(target=["name"], type_=SearchType.case_sensitive)
    q3: str = SearchField(target=["boba"])

    b: BFilter
    c: CFilter
    d: CFilter


class LeafFilter(BaseFilter):
    id: int


class MiddleFilter(BaseFilter):
    id: int
    leaf: LeafFilter


class RootFilter(BaseFilter):
    middle: MiddleFilter


class ArrayFilter(BaseFilter):
    tags: str


class ParentNodeFilter(BaseFilter):
    id: int


class NodeFilter(BaseFilter):
    parent: ParentNodeFilter


@pytest.mark.parametrize(
    "filter_, res_clause",
    [
        (FilterTest(id=1), AModel.id == 1),
        (FilterTest(id__lt=1), AModel.id < 1),
        (FilterTest(name="Alice"), AModel.name == "Alice"),
        (FilterTest(name__null=True), AModel.name.is_(None)),
        (FilterTest(name__n=["Eva"]), AModel.name.not_in(["Eva"])),
        (FilterTest(q1="a"), AModel.name.ilike("%a%")),
        (FilterTest(q1_2="a"), sa.or_(AModel.name.ilike("%a%"), AModel.id.ilike("%a%"))),
        (FilterTest(q2=["a", "b"]), sa.or_(AModel.name.like("%a%"), AModel.name.like("%b%"))),
    ]
)
def test_filter_to_column_clauses(filter_: BaseFilter, res_clause: sa.BinaryExpression[bool]) -> None:
    clauses = filter_to_column_clauses(filter_=filter_, model=AModel)
    assert len(clauses) == 1
    assert clauses[0].compare(res_clause)


@pytest.mark.parametrize(
    "filter_, exception",
    [
        (FilterTest(biba="biba"), AttributeNotFoundSaDriverError),
        (FilterTest(q3="boba"), AttributeNotFoundSaDriverError),
    ]
)
def test_filter_to_column_clauses_raises(filter_: BaseFilter, exception: type[Exception]) -> None:
    with pytest.raises(exception):
        filter_to_column_clauses(filter_=filter_, model=AModel)


def test_filter_to_column_clauses_skips_unset_fields() -> None:
    assert filter_to_column_clauses(filter_=FilterTest(), model=AModel) == []


def test_filter_to_column_clauses_uses_any_for_array_columns() -> None:
    clauses = filter_to_column_clauses(filter_=ArrayFilter(tags="admin"), model=ArrayModel)

    assert len(clauses) == 1
    assert clauses[0].compare(ArrayModel.tags.any_() == "admin")


@pytest.mark.parametrize(
    "filter_, res_join_params",
    [
        (
            FilterTest(b=BFilter(id=1)),
            JoinParams(
                target=BModelAliased,
                on_clause=sa.and_(BModelAliased.id == AModel.b_id, BModelAliased.id == 1),
            ),
        ),
    ],
)
def test_filter_to_join_targets(filter_: BaseFilter, res_join_params: JoinParams) -> None:
    joint_targets = filter_to_join_targets(filter_, AModel)
    assert sa.inspect(joint_targets[0].target).mapper == sa.inspect(res_join_params.target).mapper
    assert joint_targets[0].on_clause.compare(res_join_params.on_clause)


def test_filter_to_join_targets_recurses_through_aliased_models() -> None:
    targets = filter_to_join_targets(
        RootFilter(middle=MiddleFilter(id=2, leaf=LeafFilter(id=3))),
        RootModel,
    )

    assert len(targets) == 2
    middle_alias = targets[0].target
    leaf_alias = targets[1].target
    assert sa.inspect(middle_alias).mapper.class_ is MiddleModel
    assert sa.inspect(leaf_alias).mapper.class_ is LeafModel
    assert targets[0].on_clause.compare(
        sa.and_(RootModel.middle_id == middle_alias.id, middle_alias.id == 2),
    )
    assert targets[1].on_clause.compare(
        sa.and_(middle_alias.leaf_id == leaf_alias.id, leaf_alias.id == 3),
    )


def test_filter_to_join_targets_preserves_root_side_of_self_relationship() -> None:
    targets = filter_to_join_targets(NodeFilter(parent=ParentNodeFilter(id=2)), NodeModel)

    assert len(targets) == 1
    parent_alias = targets[0].target
    assert targets[0].on_clause.compare(
        sa.and_(NodeModel.parent_id == parent_alias.id, parent_alias.id == 2),
    )


@pytest.mark.parametrize(
    "filter_, exception",
    [
        (FilterTest(d=CFilter(id=1)), RelationshipNotFoundSaDriverError),
    ],
)
def test_filter_to_join_targets_raises(filter_: BaseFilter, exception: type[Exception]) -> None:
    with pytest.raises(exception):
        filter_to_join_targets(filter_, AModel)

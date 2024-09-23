from typing import List, Type

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


class AModel(Base):
    __tablename__ = 'a'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str]
    b_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(BModel.id))
    b: so.Mapped[BModel] = so.relationship()
    c: so.Mapped[List[CModel]] = so.relationship()


class CFilter(BaseFilter):
    id: int


class BFilter(BaseFilter):
    id: int


class FilterTest(BaseFilter):
    id: int
    id__lt: int
    name: str
    name__null: bool
    name__n: List[str]
    biba: str

    q1: str = SearchField(target=["name"])
    q1_2: str = SearchField(target=["id", "name"])
    q2: List[str] = SearchField(target=["name"], type_=SearchType.case_sensitive)
    q3: str = SearchField(target=["boba"])

    b: BFilter
    c: CFilter
    d: CFilter


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
def test_filter_to_column_clauses_raises(filter_: BaseFilter, exception: Type[Exception]) -> None:
    with pytest.raises(exception):
        filter_to_column_clauses(filter_=filter_, model=AModel)


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


@pytest.mark.parametrize(
    "filter_, exception",
    [
        (FilterTest(d=CFilter(id=1)), RelationshipNotFoundSaDriverError),
    ],
)
def test_filter_to_join_targets_raises(filter_: BaseFilter, exception: Type[Exception]) -> None:
    with pytest.raises(exception):
        filter_to_join_targets(filter_, AModel)

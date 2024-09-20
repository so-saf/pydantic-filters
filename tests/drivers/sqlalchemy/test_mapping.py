from typing import List

import pytest
import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic_filters import BaseFilter, SearchField, SearchType
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

    q1: str = SearchField(target=["name"])
    q2: List[str] = SearchField(target=["name"], type_=SearchType.case_sensitive)

    b: BFilter
    c: CFilter


@pytest.mark.parametrize(
    "filter_, res_clause",
    [
        (FilterTest(id=1), AModel.id == 1),
        (FilterTest(id__lt=1), AModel.id < 1),
        (FilterTest(name="Alice"), AModel.name == "Alice"),
        (FilterTest(name__null=True), AModel.name.is_(None)),
        (FilterTest(name__n=["Eva"]), AModel.name.not_in(["Eva"])),
        (FilterTest(q1="a"), AModel.name.ilike("%a%")),
        (FilterTest(q2=["a", "b"]), sa.or_(AModel.name.like("%a%"), AModel.name.like("%b%"))),
    ]
)
def test_filter_to_column_clauses(filter_: BaseFilter, res_clause: sa.BinaryExpression[bool]) -> None:
    clauses = filter_to_column_clauses(filter_=filter_, model=AModel)
    assert clauses[0].compare(res_clause)


@pytest.mark.parametrize(
    "filter_, res_join_params",
    [
        (
                FilterTest(b=BFilter(id=1)),
                JoinParams(target=BModel, on_clause=sa.and_(BModel.id == AModel.b_id, BModel.id == 1)),
        ),
    ],
)
def test_filter_to_column_options(filter_: BaseFilter, res_join_params: JoinParams) -> None:
    joint_targets = filter_to_join_targets(filter_, AModel)
    assert joint_targets[0].target == res_join_params.target
    assert joint_targets[0].on_clause.compare(res_join_params.on_clause)

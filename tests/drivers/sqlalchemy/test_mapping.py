from typing import List
from unittest import mock

import pytest

import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic_filters import BaseFilter, SearchField, SearchType
from pydantic_filters.drivers.sqlalchemy._main import (
    filter_to_column_clauses,
    filter_to_column_options,
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
        (FilterTest(q2=["a", "b"]), sa.or_(AModel.name.like("%a%"), AModel.name.like("%b%")))
    ]
)
def test_filter_to_column_clauses(filter_: BaseFilter, res_clause: sa.BinaryExpression[bool]):
    clauses = filter_to_column_clauses(filter_=filter_, model=AModel)
    assert clauses[0].compare(res_clause)

        
def test_filter_to_column_options():
    with mock.patch("sqlalchemy.orm.joinedload") as mock_joinedload:
        filter_to_column_options(
            filter_=FilterTest(b=BFilter(id=7), c=CFilter(id=8)),
            model=AModel,
        )
        # This is a subqueries that should be passed to so.joinedload
        b_attr: so.QueryableAttribute[bool] = mock_joinedload.call_args_list[0].args[0]
        c_attr: so.QueryableAttribute[bool] = mock_joinedload.call_args_list[1].args[0] 
        assert b_attr.impl is AModel.b.impl
        assert c_attr.impl is AModel.c.impl
        assert b_attr.expression.compare(AModel.b.and_(BModel.id == 7).expression)
        assert c_attr.expression.compare(AModel.c.and_(CModel.id == 8).expression)

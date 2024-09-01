import re

import pytest
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects.sqlite import dialect as sa_sqlite_dialect

from pydantic_filters import BaseFilter, BasePagination, BaseSort, SortByOrder
from pydantic_filters.drivers.sqlalchemy._main import (
    append_filter_to_statement,
    append_pagination_to_statement,
    append_sort_to_statement,
    append_to_statement,
)


class Base(so.DeclarativeBase):
    pass


class BModel(Base):
    __tablename__ = "b"
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)


class AModel(Base):
    __tablename__ = "a"
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)
    b_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(BModel.id))
    
    b: so.Mapped[BModel] = so.relationship()


class BFilter(BaseFilter):
    id: int
    
    
class AFilter(BaseFilter):
    id: int
    b: BFilter
    
    
def compile_statement(stmt: sa.Select) -> str:
    compiled = stmt.compile(
        dialect=sa_sqlite_dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return " ".join(re.split(r"\s+", compiled.string))


def test_append_filter_to_statement() -> None:
    stmt = append_filter_to_statement(
        statement=sa.select(AModel),
        model=AModel,
        filter_=AFilter(id=1, b=BFilter(id=2)),
    )
    expected_stmt = (
        "SELECT a.id, a.b_id, b_1.id AS id_1 "
        "FROM a JOIN b AS b_1 ON b_1.id = a.b_id AND b_1.id = 2 "
        "WHERE a.id = 1"
    )
    assert compile_statement(stmt) == expected_stmt
    

@pytest.mark.parametrize(
    "pagination, expected_stmt",
    [
        (BasePagination(),
         "SELECT a.id, a.b_id FROM a"),
        (BasePagination(limit=10),
         "SELECT a.id, a.b_id FROM a LIMIT 10 OFFSET 0"),
        (BasePagination(limit=10, offset=20),
         "SELECT a.id, a.b_id FROM a LIMIT 10 OFFSET 20"),
    ]
)
def test_append_pagination_to_statement(pagination: BasePagination, expected_stmt: str) -> None:
    stmt = append_pagination_to_statement(
        statement=sa.select(AModel),
        pagination=pagination,
    )
    assert compile_statement(stmt) == expected_stmt


@pytest.mark.parametrize(
    "sort, expected_stmt",
    [
        (BaseSort(sort_by="id"),
         "SELECT a.id, a.b_id FROM a ORDER BY a.id ASC"),
        (BaseSort(sort_by="id", sort_by_order=SortByOrder.desc),
         "SELECT a.id, a.b_id FROM a ORDER BY a.id DESC"),
    ],
)
def test_append_sort_to_statement( 
        sort: BaseSort, 
        expected_stmt: str,
) -> None:
    stmt = append_sort_to_statement(
        statement=sa.select(AModel),
        model=AModel,
        sort=sort,
    )
    assert compile_statement(stmt) == expected_stmt
    
    
def test_append_to_statement() -> None:
    stmt = append_to_statement(
        statement=sa.select(AModel),
        model=AModel,
        filter_=AFilter(id=1, b=BFilter(id=2)),
        pagination=BasePagination(limit=10, offset=20),
        sort=BaseSort(sort_by="id", sort_by_order=SortByOrder.desc)
    )
    expected_stmt = (
        "SELECT a.id, a.b_id, b_1.id AS id_1 "
        "FROM a JOIN b AS b_1 ON b_1.id = a.b_id AND b_1.id = 2 "
        "WHERE a.id = 1 "
        "ORDER BY a.id DESC "
        "LIMIT 10 OFFSET 20"
    )
    assert compile_statement(stmt) == expected_stmt

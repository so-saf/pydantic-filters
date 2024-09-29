import re
from typing import Type

import pytest
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects.sqlite import dialect as sa_sqlite_dialect

from pydantic_filters import (
    BaseFilter,
    OffsetPagination,
    BaseSort,
    SortByOrder,
    BasePagination,
    PagePagination,
)
from pydantic_filters.drivers.sqlalchemy._exceptions import (
    AttributeNotFoundSaDriverError,
    SupportSaDriverError,
)
from pydantic_filters.drivers.sqlalchemy._main import (
    append_filter_to_statement,
    append_pagination_to_statement,
    append_sort_to_statement,
    append_to_statement,
    get_count_statement,
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
    b2_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(BModel.id))
    
    b: so.Mapped[BModel] = so.relationship(foreign_keys="AModel.b_id")
    b2: so.Mapped[BModel] = so.relationship(foreign_keys="AModel.b2_id")
    
    
class ABModel(Base):
    __tablename__ = "ab"
    __table_args__ = (
        sa.PrimaryKeyConstraint("a_id", "b_id"),
    )
    
    a_id: so.Mapped[int]
    b_id: so.Mapped[int]


class BFilter(BaseFilter):
    id: int
    
    
class AFilter(BaseFilter):
    id: int
    b: BFilter
    b2: BFilter
    
    
def compile_statement(stmt: sa.Select) -> str:
    compiled = stmt.compile(
        dialect=sa_sqlite_dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return " ".join(re.split(r"\s+", compiled.string))


@pytest.mark.parametrize(
    "filter_, expected_stmt",
    [
        (
            AFilter(id=1, b=BFilter(id=2)),
            (
                "SELECT a.id, a.b_id, a.b2_id "
                "FROM a "
                "JOIN b AS b_1 ON a.b_id = b_1.id AND b_1.id = 2 "
                "WHERE a.id = 1"
            ),
        ),
        (
            AFilter(id=1, b=BFilter(id=2), b2=BFilter(id=3)),
            (
                "SELECT a.id, a.b_id, a.b2_id "
                "FROM a "
                "JOIN b AS b_1 ON a.b_id = b_1.id AND b_1.id = 2 "
                "JOIN b AS b_2 ON a.b2_id = b_2.id AND b_2.id = 3 "
                "WHERE a.id = 1"
            ),
        ),
    ]
)
def test_append_filter_to_statement(filter_: BaseFilter, expected_stmt: str) -> None:
    stmt = append_filter_to_statement(sa.select(AModel), AModel, filter_)
    assert compile_statement(stmt) == expected_stmt
    

@pytest.mark.parametrize(
    "pagination, expected_stmt",
    [
        (OffsetPagination(limit=10), "SELECT a.id, a.b_id, a.b2_id FROM a LIMIT 10 OFFSET 0"),
        (OffsetPagination(limit=10, offset=20), "SELECT a.id, a.b_id, a.b2_id FROM a LIMIT 10 OFFSET 20"),
        (PagePagination(page=1, per_page=10), "SELECT a.id, a.b_id, a.b2_id FROM a LIMIT 10 OFFSET 0"),
        (PagePagination(page=10, per_page=10), "SELECT a.id, a.b_id, a.b2_id FROM a LIMIT 10 OFFSET 90"),
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
        (BaseSort(), 
         "SELECT a.id, a.b_id, a.b2_id FROM a"),
        (BaseSort(sort_by="id"),
         "SELECT a.id, a.b_id, a.b2_id FROM a ORDER BY a.id ASC"),
        (BaseSort(sort_by="id", sort_by_order=SortByOrder.desc),
         "SELECT a.id, a.b_id, a.b2_id FROM a ORDER BY a.id DESC"),
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
    
    
@pytest.mark.parametrize(
    "sort, exception",
    [
        (BaseSort(sort_by="biba"), AttributeNotFoundSaDriverError)
    ],
)
def test_append_sort_to_statement_raises( 
        sort: BaseSort,
        exception: Type[Exception],
) -> None:
    with pytest.raises(exception):
        append_sort_to_statement(
            statement=sa.select(AModel),
            model=AModel,
            sort=sort,
        )
    
    
def test_append_to_statement() -> None:
    stmt = append_to_statement(
        statement=sa.select(AModel),
        model=AModel,
        filter_=AFilter(id=1, b=BFilter(id=2)),
        pagination=OffsetPagination(limit=10, offset=20),
        sort=BaseSort(sort_by="id", sort_by_order=SortByOrder.desc)
    )
    expected_stmt = (
        "SELECT a.id, a.b_id, a.b2_id "
        "FROM a JOIN b AS b_1 ON a.b_id = b_1.id AND b_1.id = 2 "
        "WHERE a.id = 1 "
        "ORDER BY a.id DESC "
        "LIMIT 10 OFFSET 20"
    )
    assert compile_statement(stmt) == expected_stmt
    
    
def test_get_count_statement() -> None:
    stmt = get_count_statement(
        model=AModel,
        filter_=AFilter(id=1, b=BFilter(id=2)),
    )
    expected_stmt = (
        "SELECT count(DISTINCT a.id) AS count_1 "
        "FROM a JOIN b AS b_1 ON a.b_id = b_1.id AND b_1.id = 2 "
        "WHERE a.id = 1"
    )
    assert compile_statement(stmt) == expected_stmt


def test_get_count_statement_raises() -> None:
    with pytest.raises(SupportSaDriverError):
        get_count_statement(
            model=ABModel,
            filter_=AFilter(id=1, b=BFilter(id=2)),
        )

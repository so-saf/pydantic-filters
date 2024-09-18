from typing import Optional, Type, TypeVar

import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic_filters import (
    BaseFilter,
    BaseSort,
    PaginationInterface,
    SortByOrder,
)

from ._exceptions import AttributeNotFoundSaDriverError
from ._mapping import filter_to_column_clauses, filter_to_column_options

_Filter = TypeVar("_Filter", bound=BaseFilter)
_Pagination = TypeVar("_Pagination", bound=PaginationInterface)
_Sort = TypeVar("_Sort", bound=BaseSort)
_Model = TypeVar("_Model", bound=so.DeclarativeBase)
_T = TypeVar("_T")


def append_filter_to_statement(
        statement: sa.Select[_T],
        model: Type[_Model],
        filter_: _Filter,
) -> sa.Select[_T]:
    clauses = filter_to_column_clauses(filter_, model)
    if clauses:
        statement = statement.where(*clauses)

    options = filter_to_column_options(filter_, model)
    if options:
        statement = statement.options(*options)

    return statement


def append_pagination_to_statement(
        statement: sa.Select[_T],
        pagination: _Pagination,
) -> sa.Select[_T]:

    return (
        statement
        .limit(pagination.get_limit())
        .offset(pagination.get_offset())
    )


def append_sort_to_statement(
        statement: sa.Select[_T],
        model: Type[_Model],
        sort: _Sort,
) -> sa.Select[_T]:

    if sort.sort_by is None:
        return statement

    try:
        column: sa.ColumnElement = getattr(model, str(sort.sort_by))
    except AttributeError as e:
        raise AttributeNotFoundSaDriverError(
            f"{sort.__class__.__name__}.sort_by: "
            f"Column {model.__name__}.{sort.sort_by} not found",
        ) from e

    return statement.order_by(
        sa.desc(column) if sort.sort_by_order == SortByOrder.desc else sa.asc(column),
    )


def append_to_statement(
        statement: sa.Select[_T],
        model: Type[_Model],
        *,
        filter_: Optional[_Filter] = None,
        sort: Optional[_Sort] = None,
        pagination: Optional[_Pagination] = None,
) -> sa.Select[_T]:

    if filter_ is not None:
        statement = append_filter_to_statement(statement=statement, model=model, filter_=filter_)
    if sort is not None:
        statement = append_sort_to_statement(statement=statement, model=model, sort=sort)
    if pagination is not None:
        statement = append_pagination_to_statement(statement=statement, pagination=pagination)

    return statement

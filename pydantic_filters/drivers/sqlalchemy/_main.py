from typing import Optional, Tuple, Type, TypeVar

import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic_filters import (
    BaseFilter,
    BasePagination,
    BaseSort,
    SortByOrder,
)

from ._exceptions import AttributeNotFoundSaDriverError, SupportSaDriverError
from ._mapping import filter_to_column_clauses, filter_to_join_targets

_Filter = TypeVar("_Filter", bound=BaseFilter)
_Pagination = TypeVar("_Pagination", bound=BasePagination)
_Sort = TypeVar("_Sort", bound=BaseSort)
_Model = TypeVar("_Model", bound=so.DeclarativeBase)
_T = TypeVar("_T")


def append_filter_to_statement(
        statement: sa.Select[_T],
        model: Type[_Model],
        filter_: _Filter,
) -> sa.Select[_T]:
    """
    Append filtering to statement.

    Args:
        statement: Some select statement.
        model: Declaratively defined model.
        filter_: Filter object.

    Raises:
        AttributeNotFoundSaDriverError: Attribute not found
        RelationshipNotFoundSaDriverError:  Relationship not found
    """

    join_targets = filter_to_join_targets(filter_, model)
    for target in join_targets:
        statement = statement.join(
            target=target.target,
            onclause=target.on_clause,
        )

    clauses = filter_to_column_clauses(filter_, model)
    if clauses:
        statement = statement.where(*clauses)

    return statement


def append_pagination_to_statement(
        statement: sa.Select[_T],
        pagination: _Pagination,
) -> sa.Select[_T]:
    """
    Append pagination to statement.

    Args:
        statement: Some select statement.
        pagination: Pagination object.

    Raises:
        AttributeNotFoundSaDriverError: Attribute not found
    """

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
    """
    Append sorting to statement.

    Args:
        statement: Some select statement.
        model: Declaratively defined model.
        sort: Sort object.

    Raises:
        AttributeNotFoundSaDriverError: Attribute not found
    """

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
    """
    All in one function.

    Args:
        statement: Some select statement.
        model: Declaratively defined model.
        filter_: Filter object.
        sort: Sort object.
        pagination: Pagination object.

    Raises:
        AttributeNotFoundSaDriverError: Attribute not found
        RelationshipNotFoundSaDriverError:  Relationship not found
    """

    if filter_ is not None:
        statement = append_filter_to_statement(statement=statement, model=model, filter_=filter_)
    if sort is not None:
        statement = append_sort_to_statement(statement=statement, model=model, sort=sort)
    if pagination is not None:
        statement = append_pagination_to_statement(statement=statement, pagination=pagination)

    return statement


def get_count_statement(
        model: Type[_Model],
        filter_: _Filter,
) -> sa.Select[_T]:
    """
    Get count statement.

    Args:
        model: Declaratively defined model.
        filter_: Filter object.

    Raises:
        AttributeNotFoundSaDriverError: Attribute not found.
        RelationshipNotFoundSaDriverError:  Relationship not found.
        SupportSaDriverError: Composite primary keys are not supported.
    """

    primary_key: Tuple[sa.ColumnElement, ...] = sa.inspect(model).primary_key
    if len(primary_key) > 1:
        raise SupportSaDriverError("Composite primary keys are not supported")

    statement = sa.select(
        sa.func.count(
            sa.distinct(primary_key[0]),
        ),
    )

    return append_filter_to_statement(statement, model, filter_)

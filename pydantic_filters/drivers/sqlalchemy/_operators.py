from collections.abc import Callable
from typing import Any, TypeAlias

import sqlalchemy as sa

from pydantic_filters import FilterType, SearchType

ClauseOperator: TypeAlias = Callable[
    [sa.ColumnElement, bool, Any],
    sa.ColumnElement[bool],
]


def _op_from_method(method: str) -> ClauseOperator:
    def _op(
            column: sa.ColumnElement,
            is_sequence: bool,
            obj: Any,
    ) -> sa.ColumnElement[bool]:
        method_ = getattr(column, method)
        if is_sequence:
            expressions = [method_(o) for o in obj]
            return sa.or_(*expressions) if expressions else sa.false()
        return getattr(column, method)(obj)

    return _op


def _op_eq(
        column: sa.ColumnElement, is_sequence: bool, obj: Any,
) -> sa.ColumnElement[bool]:
    return column.in_(obj) if is_sequence else column == obj


def _op_ne(
        column: sa.ColumnElement, is_sequence: bool, obj: Any,
) -> sa.ColumnElement[bool]:
    return column.not_in(obj) if is_sequence else column != obj


def _op_null(
        column: sa.ColumnElement, is_sequence: bool, obj: Any,
) -> sa.ColumnElement[bool]:
    expression = any(obj) if is_sequence else bool(obj)
    return column.is_(None) if expression else column.is_not(None)


def _op_case_sensitive_search(
        column: sa.ColumnElement, is_sequence: bool, obj: Any,
) -> sa.ColumnElement[bool]:
    return _op_from_method("like")(
        column,
        is_sequence,
        [f"%{o}%" for o in obj] if is_sequence else f"%{obj}%",
    )


def _op_case_insensitive_search(
        column: sa.ColumnElement, is_sequence: bool, obj: Any,
) -> sa.ColumnElement[bool]:
    return _op_from_method("ilike")(
        column,
        is_sequence,
        [f"%{o}%" for o in obj] if is_sequence else f"%{obj}%",
    )


_filter_type_to_operator_map: dict[FilterType, ClauseOperator] = {
    FilterType.eq: _op_eq,
    FilterType.ne: _op_ne,
    FilterType.gt: _op_from_method("__gt__"),
    FilterType.ge: _op_from_method("__ge__"),
    FilterType.lt: _op_from_method("__lt__"),
    FilterType.le: _op_from_method("__le__"),
    FilterType.like: _op_from_method("like"),
    FilterType.ilike: _op_from_method("ilike"),
    FilterType.null: _op_null,
}

_search_type_to_operator_map: dict[SearchType, ClauseOperator] = {
    SearchType.case_sensitive: _op_case_sensitive_search,
    SearchType.case_insensitive: _op_case_insensitive_search,
}


def get_filter_operator(type_: FilterType) -> ClauseOperator:
    return _filter_type_to_operator_map[type_]


def get_search_operator(type_: SearchType) -> ClauseOperator:
    return _search_type_to_operator_map[type_]

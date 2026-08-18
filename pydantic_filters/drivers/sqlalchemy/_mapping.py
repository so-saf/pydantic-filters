from dataclasses import dataclass
from typing import Any, TypeVar, cast

import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.sql.util import ClauseAdapter

from pydantic_filters import BaseFilter

from ._exceptions import AttributeNotFoundSaDriverError, RelationshipNotFoundSaDriverError
from ._operators import get_filter_operator, get_search_operator

_Filter = TypeVar("_Filter", bound=BaseFilter)
_Model = TypeVar("_Model", bound=so.DeclarativeBase)


@dataclass
class JoinParams:
    target: Any
    on_clause: sa.ColumnExpressionArgument


def _get_relationship_join_clauses(
        relationship: so.Relationship,
        model: Any,
        inspected: Any,
        nested_class: type[so.DeclarativeBase],
        nested_class_aliased: so.util.AliasedClass[Any],
) -> tuple[list[JoinParams], list[sa.ColumnExpressionArgument]]:
    if relationship.secondary is not None:
        primary_join = relationship.primaryjoin
        if not inspected.is_mapper:
            primary_join = ClauseAdapter(inspected.selectable).traverse(primary_join)

        secondary_join = ClauseAdapter(sa.inspect(nested_class_aliased).selectable).traverse(
            relationship.secondaryjoin,
        )
        assert primary_join is not None
        assert secondary_join is not None
        return [JoinParams(target=relationship.secondary, on_clause=primary_join)], [secondary_join]

    clauses: list[sa.ColumnExpressionArgument] = []
    for local, remote in relationship.local_remote_pairs or ():
        if local.table is model.__table__:
            local = getattr(model, cast("str", local.key))
        if remote.table is nested_class.__table__:
            remote = getattr(nested_class_aliased, cast("str", remote.key))
        clauses.append(local == remote)

    return [], clauses


def filter_to_column_clauses(
        filter_: _Filter,
        model: type[_Model] | so.util.AliasedClass[_Model],
) -> list[sa.ColumnExpressionArgument]:
    """Data from the filter to the list of expressions for SQLAlchemy

    **Example**

    >>> class Base(so.DeclarativeBase):
    ...     pass
    ...
    >>> class MyModel(Base):
    ...     __tablename__ = "mymodels"
    ...     id: so.Mapped[int] = so.mapped_column(primary_key=True)
    ...     name: so.Mapped[str]
    ...
    >>> class MyFilter(BaseFilter):
    ...     name: list[str]
    ...     name__n: list[str]
    ...
    >>> filter_to_column_clauses(
    ...     filter_=MyFilter(name=["Alice", "Bob"], name__n=["Eva"]),
    ...     model=MyModel,
    ... )
    [
        MyModel.name.in_(["Alice", "Bob"]),
        MyModel.name.not_in(["Eva"]),
    ]
    """

    clauses: list[sa.ColumnExpressionArgument] = []
    included_items: dict[str, Any] = filter_.model_dump(exclude_unset=True)

    for key, filter_field_info in filter_.filter_fields.items():
        if key not in included_items:
            continue

        try:
            assert filter_field_info.target is not None
            column: sa.ColumnElement = getattr(model, filter_field_info.target)
        except AttributeError as e:
            raise AttributeNotFoundSaDriverError(
                f"{filter_.__class__.__name__}.{key}: "
                f"Column {model.__name__}.{filter_field_info.target} not found",
            ) from e

        if isinstance(column.type, sa.ARRAY):
            column = column.any_()

        assert filter_field_info.type is not None
        assert filter_field_info.is_sequence is not None
        operator = get_filter_operator(filter_field_info.type)
        clauses.append(
            operator(column, filter_field_info.is_sequence, included_items[key]),
        )

    for key, search_field_info in filter_.search_fields.items():
        if key not in included_items:
            continue

        assert search_field_info.type is not None
        assert search_field_info.is_sequence is not None
        operator = get_search_operator(search_field_info.type)
        search_clauses: list[sa.ColumnExpressionArgument] = []

        for t in search_field_info.target:
            try:
                column = getattr(model, t)
            except AttributeError as e:
                raise AttributeNotFoundSaDriverError(
                    f"{filter_.__class__.__name__}.{key}: "
                    f"Column {model.__name__}.{t} not found",
                ) from e

            search_clauses.append(
                operator(column, search_field_info.is_sequence, included_items[key]),
            )

        clauses.append(
            sa.or_(*search_clauses),
        )

    return clauses


def filter_to_join_targets(
        filter_: _Filter,
        model: type[so.DeclarativeBase] | so.util.AliasedClass[Any],
) -> list[JoinParams]:
    """Get targets to join"""

    inspected = sa.inspect(model)
    assert inspected is not None
    try:
        mapper = inspected if inspected.is_mapper else inspected.mapper
    except AttributeError:
        mapper = inspected

    targets = []

    for field_name in filter_.nested_filters:
        nested_filter = getattr(filter_, field_name)
        if not nested_filter:
            continue

        try:
            relationship: so.Relationship = getattr(mapper.relationships, field_name)
        except AttributeError as e:
            raise RelationshipNotFoundSaDriverError(
                f"{filter_.__class__.__name__}.{field_name}: "
                f"Relationship {model.__name__}.{field_name} not found",
            ) from e

        assert relationship.entity is not None
        nested_class = cast("type[so.DeclarativeBase]", relationship.entity.class_)
        nested_class_aliased = cast("so.util.AliasedClass[Any]", so.aliased(nested_class))
        secondary_targets, clauses = _get_relationship_join_clauses(
            relationship,
            model,
            inspected,
            nested_class,
            nested_class_aliased,
        )
        targets.extend(secondary_targets)
        clauses.extend(
            filter_to_column_clauses(filter_=nested_filter, model=nested_class_aliased),
        )
        targets.append(
            JoinParams(
                target=nested_class_aliased,
                on_clause=sa.and_(*clauses),
            ),
        )

        nested_targets = filter_to_join_targets(filter_=nested_filter, model=nested_class_aliased)
        targets.extend(nested_targets)

    return targets

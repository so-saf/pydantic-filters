from dataclasses import dataclass
from typing import Any, Dict, List, Type, TypeVar, Union, cast

import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic_filters import BaseFilter

from ._exceptions import AttributeNotFoundSaDriverError, RelationshipNotFoundSaDriverError
from ._operators import get_filter_operator, get_search_operator

_Filter = TypeVar("_Filter", bound=BaseFilter)
_Model = TypeVar("_Model", bound=so.DeclarativeBase)


@dataclass
class JoinParams:
    target: Union[Type[so.DeclarativeBase], so.util.AliasedClass]
    on_clause: sa.ColumnExpressionArgument


def filter_to_column_clauses(
        filter_: _Filter,
        model: Union[Type[_Model], so.util.AliasedClass],
) -> List[sa.ColumnExpressionArgument]:
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
    ...     name: List[str]
    ...     name__n: List[str]
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

    clauses = []
    included_items: Dict[str, Any] = filter_.model_dump(exclude_unset=True)

    for key, filter_field_info in filter_.filter_fields.items():
        if key not in included_items:
            continue

        try:
            column: sa.ColumnElement = getattr(model, filter_field_info.target)
        except AttributeError as e:
            raise AttributeNotFoundSaDriverError(
                f"{filter_.__class__.__name__}.{key}: "
                f"Column {model.__name__}.{filter_field_info.target} not found",
            ) from e

        if isinstance(column.type, sa.ARRAY):
            column = column.any_()

        operator = get_filter_operator(filter_field_info.type)
        clauses.append(
            operator(column, filter_field_info.is_sequence, included_items[key]),
        )

    for key, search_field_info in filter_.search_fields.items():
        if key not in included_items:
            continue

        operator = get_search_operator(search_field_info.type)
        search_clauses = []

        for t in search_field_info.target:
            try:
                column = getattr(model, str(t))
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
        model: Type[so.DeclarativeBase],
) -> List[JoinParams]:
    """Get targets to join"""

    targets = []
    mapper: so.Mapper = sa.inspect(model)

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

        nested_class: Type[_Model] = relationship.entity.class_
        nested_class_aliased: so.util.AliasedClass = so.aliased(nested_class)

        def replace_by_aliased(__c: sa.Column) -> sa.Column:
            if __c.table is nested_class.__table__:
                return getattr(nested_class_aliased, __c.key)
            return __c

        clauses = cast(
            List[sa.ColumnExpressionArgument],
            [
                replace_by_aliased(pair[0]) == replace_by_aliased(pair[1])
                for pair in relationship.local_remote_pairs],
        )
        clauses.extend(
            filter_to_column_clauses(filter_=nested_filter, model=nested_class_aliased),
        )
        targets.append(
            JoinParams(
                target=nested_class_aliased,
                on_clause=sa.and_(*clauses),
            ),
        )

        nested_targets = filter_to_join_targets(filter_=nested_filter, model=nested_class)
        targets.extend(nested_targets)

    return targets

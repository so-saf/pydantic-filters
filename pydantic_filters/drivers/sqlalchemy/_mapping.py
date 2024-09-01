from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic_filters import (
    BaseFilter,
)

from ._exceptions import AttributeNotFoundSaDriverError, RelationshipNotFoundSaDriverError
from ._operators import get_filter_operator, get_search_operator

if TYPE_CHECKING:
    from sqlalchemy.sql.base import ExecutableOption


_Filter = TypeVar("_Filter", bound=BaseFilter)
_Model = TypeVar("_Model", bound=so.DeclarativeBase)


__all__ = (
    "filter_to_column_clauses",
    "filter_to_column_options",
)


def filter_to_column_clauses(
        filter_: _Filter,
        model: Type[_Model],
) -> List[Union[sa.ColumnElement[bool], sa.BinaryExpression[bool]]]:
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

        for t in search_field_info.target:
            try:
                column = getattr(model, str(t))
            except AttributeError as e:
                raise AttributeNotFoundSaDriverError(
                    f"{filter_.__class__.__name__}.{key}: "
                    f"Column {model.__name__}.{t} not found",
                ) from e

            clauses.append(
                operator(column, search_field_info.is_sequence, included_items[key]),
            )

    return clauses


def filter_to_column_options(
        filter_: _Filter,
        model: Type[so.DeclarativeBase],
) -> List["ExecutableOption"]:
    """Does the same as filter_to_columns_clauses,
    but for nested filters by left-joins of their corresponding relationships in the model
    """

    options = []
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

        nested_mapper: so.Mapper = relationship.entity

        clauses = filter_to_column_clauses(
            filter_=nested_filter,
            model=nested_mapper.class_,
        )

        option = so.joinedload(
            relationship.class_attribute.and_(*clauses),
            innerjoin=True,
        )
        nested_options = filter_to_column_options(
            filter_=nested_filter,
            model=nested_mapper.class_,
        )

        if nested_options:
            option = option.options(*nested_options)

        options.append(option)

    return options

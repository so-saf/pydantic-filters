from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from pydantic_core import PydanticUndefined

from ._types import FilterType, FilterTypeLiteral, SearchType, SearchTypeLiteral


class BaseField:
    __field_kwargs: Optional[Dict[str, Any]]

    __slots__ = (
        "__field_kwargs",
    )

    def __init__(self, *, field_kwargs: Optional[Dict[str, Any]] = None) -> None:
        self.__field_kwargs = field_kwargs or {}

    @property
    def field_kwargs(self) -> Dict[str, Any]:
        """
        Get arguments for pydantic.FieldInfo creating.
        """
        return self.__field_kwargs

    def __eq__(self, __value: Any) -> bool:  # noqa: ANN401
        return isinstance(__value, self.__class__) and all(
            getattr(self, item) == getattr(__value, item)
            for item in self.__slots__
            if not item.startswith("__")
        )

    def __repr_args(self) -> List[Tuple[str, Any]]:
        attrs = (
            (s, getattr(self, s))
            for s in self.__slots__
            if not s.startswith("__")
        )
        return [
            (a, v)
            for a, v in attrs
            if v is not None
        ]

    def __repr_str(self, join_str: str) -> str:
        return join_str.join(
            repr(v) if a is None else f'{a}={v!r}'
            for a, v in self.__repr_args()
        )

    def __str__(self) -> str:
        return self.__repr_str(' ')

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.__repr_str(", ")})'


class FilterFieldInfo(BaseField):
    """This class holds information about a filter field.

    FilterFieldInfo is used for any filter field definition regardless of whether the
    [`FilterField()`][pydantic_filters.filter._fields.FilterField] function is explicitly used.

    Warning:
        You generally shouldn't be creating `FilterFieldInfo` directly,
        you'll only need to use it when accessing
        [`BaseFilter`][pydantic_filters.filter._base.BaseFilter].filter_fields internals.

    Args:
        target: Target for filtering.
        type_: Filter type.
        is_sequence: Is the field annotated as sequence.
        field_kwargs: Other arguments to pass to pydantic.Field.
    """

    __slots__ = (
        "target",
        "type",
        "is_sequence",
    )

    def __init__(
            self,
            *,
            target: Optional[str] = None,
            type_: Optional[FilterType] = None,
            is_sequence: Optional[bool] = None,
            field_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.target = target
        self.type = type_
        self.is_sequence = is_sequence
        super().__init__(
            field_kwargs=field_kwargs,
        )


class SearchFieldInfo(BaseField):
    """This class holds information about a search field.

    SearchFieldInfo is used for any search field definition regardless
    of whether the [`SearchField()`][pydantic_filters.filter._fields.SearchField] function is explicitly used.

    Warning:
        You generally shouldn't be creating `SearchFieldInfo` directly,
        you'll only need to use it when accessing
        [`BaseFilter`][pydantic_filters.filter._base.BaseFilter].search_fields internals.

    Args:
        target: Target for search.
        type_: Search type.
        is_sequence: Is the field annotated as sequence.
        field_kwargs: Other arguments to pass to pydantic.Field.
    """

    __slots__ = (
        "target",
        "type",
        "is_sequence",
    )

    def __init__(
            self,
            *,
            target: Sequence[str],
            type_: Optional[SearchType] = None,
            is_sequence: Optional[bool] = None,
            field_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:

        if not target:
            raise ValueError("Target must contain at least one value")

        self.target = target
        self.type = type_
        self.is_sequence = is_sequence
        super().__init__(
            field_kwargs=field_kwargs,
        )


def FilterField(  # noqa: N802
        default: Any = PydanticUndefined,  # noqa: ANN401
        *,
        target: Optional[str] = None,
        type_: Union[FilterTypeLiteral, FilterType, None] = None,
        **field_kwargs: Any,  # noqa: ANN003
) -> FilterFieldInfo:
    """
    Create a field for objects that can be configured.

    Used to provide extra information about a field.

    Args:
        default: Default value to be passed to pydantic.Field.
        target: Target for filtering.
        type_: Filter type.
        **field_kwargs: Other arguments to pass to pydantic.Field.
    """

    field_kwargs["default"] = default
    if type_ is not None:
        type_ = FilterType(type_)

    return FilterFieldInfo(
        type_=type_,
        target=target,
        field_kwargs=field_kwargs,
    )


def SearchField(  # noqa: N802
        default: Any = PydanticUndefined,  # noqa: ANN401
        *,
        target: Sequence[str],
        type_: Union[SearchTypeLiteral, SearchType, None] = None,
        **field_kwargs: Any,  # noqa: ANN003
) -> SearchFieldInfo:
    """
    Create a field for objects that can be configured.

    Used to provide extra information about a field.

    Args:
        default: Default value to be passed to pydantic.Field.
        target: Target for search.
        type_: Search type.
        **field_kwargs: Other arguments to pass to pydantic.Field.
    """

    field_kwargs["default"] = default
    if type_ is not None:
        type_ = SearchType(type_)

    return SearchFieldInfo(
        type_=type_,
        target=target,
        field_kwargs=field_kwargs,
    )

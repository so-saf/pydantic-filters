from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from pydantic_core import PydanticUndefined

from ._types import FilterType, FilterTypeLiteral, SearchType, SearchTypeLiteral


class _BaseField:
    __field_kwargs: Optional[Dict[str, Any]]

    __slots__ = (
        "__field_kwargs",
    )

    def __init__(self, *, field_kwargs: Optional[Dict[str, Any]] = None) -> None:
        self.__field_kwargs = field_kwargs or {}

    @property
    def field_kwargs(self) -> Dict[str, Any]:
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


class FilterFieldInfo(_BaseField):

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


class SearchFieldInfo(_BaseField):

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
        **field_kwargs,  # noqa: ANN003
) -> FilterFieldInfo:
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
        **field_kwargs,  # noqa: ANN003
) -> SearchFieldInfo:
    field_kwargs["default"] = default
    if type_ is not None:
        type_ = SearchType(type_)

    return SearchFieldInfo(
        type_=type_,
        target=target,
        field_kwargs=field_kwargs,
    )

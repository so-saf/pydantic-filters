from copy import deepcopy
from enum import Enum
from typing import Dict, Literal

from typing_extensions import TypeAlias


class FilterType(str, Enum):
    """Type of filter operation."""

    eq = "eq"
    """Equal"""
    ne = "ne"
    """Not equal"""
    null = "null"
    """Is null"""
    gt = "gt"
    """Grater than"""
    ge = "ge"
    """Grater than or equal"""
    lt = "lt"
    """Lower than"""
    le = "le"
    """Lower than or equal"""
    like = "like"
    """Case-sensitive matching"""
    ilike = "ilike"
    """Case-insensitive matching"""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.value}"


class SearchType(str, Enum):
    """
    Type of search operation.
    """

    case_sensitive = "case_sensitive"
    """Case sensitive"""
    case_insensitive = "case_insensitive"
    """Case insensitive"""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.value}"


FilterTypeLiteral: TypeAlias = Literal[
    "eq",
    "ne",
    "null",
    "gt",
    "ge",
    "lt",
    "le",
    "like",
    "ilike",
]
"""
Literal alias for [`FilterType`][pydantic_filters.filter._types.FilterType]
"""

SearchTypeLiteral: TypeAlias = Literal[
    "case_sensitive",
    "case_insensitive",
]
"""
Literal alias for [`SearchType`][pydantic_filters.filter._types.SearchType]
"""

_suffixes_map: Dict[str, FilterType] = {
    "eq": FilterType.eq,
    "n": FilterType.ne,
    "ne": FilterType.ne,
    "neq": FilterType.ne,
    "null": FilterType.null,
    "isnull": FilterType.null,
    "gt": FilterType.gt,
    "ge": FilterType.ge,
    "gte": FilterType.ge,
    "lt": FilterType.lt,
    "le": FilterType.le,
    "lte": FilterType.le,
    "l": FilterType.like,
    "like": FilterType.like,
    "il": FilterType.ilike,
    "ilike": FilterType.ilike,
}


def get_suffixes_map() -> Dict[str, FilterType]:
    """
    Returns the standard set of synonyms defined in
    [`_suffixes_map`][pydantic_filters.filter._types._suffixes_map]
    """
    return deepcopy(_suffixes_map)

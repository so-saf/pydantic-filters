from copy import deepcopy
from enum import Enum
from typing import Dict, Literal

from typing_extensions import TypeAlias


class FilterType(str, Enum):
    eq = "eq"
    ne = "ne"
    null = "null"
    gt = "gt"
    ge = "ge"
    lt = "lt"
    le = "le"
    like = "like"
    ilike = "ilike"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.value}"


class SearchType(str, Enum):
    case_sensitive = "case_sensitive"
    case_insensitive = "case_insensitive"

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

SearchTypeLiteral: TypeAlias = Literal[
    "case_sensitive",
    "case_insensitive",
]

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
    return deepcopy(_suffixes_map)

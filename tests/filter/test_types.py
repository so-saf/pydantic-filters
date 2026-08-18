from typing import get_args

import pytest

from pydantic_filters.filter._types import (
    FilterType, 
    SearchType, 
    FilterTypeLiteral, 
    SearchTypeLiteral, 
    get_suffixes_map,
)


@pytest.mark.parametrize(
    "literal, enum",
    [
        (FilterTypeLiteral, FilterType),
        (SearchTypeLiteral, SearchType),
    ]
)
def test_fullness_literal(literal, enum) -> None:
    assert set(get_args(literal)) == set(enum)
    

def test_fullness_suffixes_map() -> None:
    assert set(get_suffixes_map().values()) == set(FilterType)


def test_get_suffixes_map_returns_an_independent_copy() -> None:
    suffixes = get_suffixes_map()
    suffixes["custom"] = FilterType.eq
    suffixes.pop("eq")

    fresh_suffixes = get_suffixes_map()
    assert "custom" not in fresh_suffixes
    assert fresh_suffixes["eq"] is FilterType.eq


@pytest.mark.parametrize("enum_value", [*FilterType, *SearchType])
def test_enum_repr_is_stable(enum_value) -> None:
    assert repr(enum_value) == f"{enum_value.__class__.__name__}.{enum_value.value}"

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

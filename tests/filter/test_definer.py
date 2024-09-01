from contextlib import nullcontext as does_not_raise
from typing import ContextManager

import pytest

from pydantic_filters.filter._types import FilterType
from pydantic_filters.filter._definer import FilterTypeDefiner


@pytest.mark.parametrize(
    "delimiter, expectation",
    [
        ("", pytest.raises(ValueError)),
        ("_", pytest.raises(ValueError)),
        ("__", does_not_raise()),
        ("___", does_not_raise()),
    ]
)
def test_init(
        delimiter: str,
        expectation: ContextManager,
) -> None:
    with expectation:
        FilterTypeDefiner(delimiter, FilterType.eq, {})
        
        
@pytest.fixture
def definer():
    return FilterTypeDefiner(
        delimiter="__",
        default=FilterType.eq,
        suffixes_map={
            "n": FilterType.ne,
            "lt": FilterType.lt,
        }
    )


@pytest.mark.parametrize(
    "target, res_name, res_type",
    [
        ("name__n", "name", FilterType.ne),
        ("name__lt", "name", FilterType.lt),
        ("name", "name", FilterType.eq),
        ("name__asdf", "name__asdf", FilterType.eq),
    ]
)
def test_define(
        definer: FilterTypeDefiner,
        target: str, 
        res_name: str, 
        res_type: FilterType,
) -> None:
    assert definer(target) == (res_name, res_type)


@pytest.mark.parametrize(
    "delimiter, target, res_name",
    [
        ("__", "name__eq", "name"),
        ("___", "name___eq", "name"),
        ("__", "name___eq", "name_"),
    ]
)
def test_delimiter_define(delimiter: str, target: str, res_name: str) -> None:
    definer = FilterTypeDefiner(
        delimiter=delimiter,
        default=FilterType.eq,
        suffixes_map={"eq": FilterType.eq},
    )
    assert res_name == definer(target)[0]

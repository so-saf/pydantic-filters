from typing import Any
from unittest import mock

import pytest
from pydantic.fields import FieldInfo

from pydantic_filters import BaseFilter, SearchField
from pydantic_filters.plugins._utils import (
    add_prefix,
    remove_prefix,
    squash_filter,
    inflate_filter,
)


@pytest.mark.parametrize(
    "item, prefix, delimiter, res",
    [
        ("a", "b", "__", "b__a"),
        ("a", "", ..., "a"),
        ("a", "b", "", "ba"),
    ]
)
def test_add_prefix(item: str, prefix: str, delimiter: str, res: str):
    assert add_prefix(item, prefix, delimiter) == res
    
    
@pytest.mark.parametrize(
    "item, prefix, delimiter, res",
    [
        ("b__a", "b", "__", "a"),
        ("a", "", ..., "a"),
        ("ba", "b", "", "a"),
        ("billing__a", "b", "__", "billing__a"),
        ("other__a", "b", "__", "other__a"),
    ]
)
def test_remove_prefix(item: str, prefix: str, delimiter: str, res: str):
    assert remove_prefix(item, prefix, delimiter) == res


class DeepNestedFilter(BaseFilter):
    e: int


class NestedFilter(BaseFilter):
    c: int
    d: DeepNestedFilter


class FilterTest(BaseFilter):
    a: int
    b: NestedFilter
    

@mock.patch.object(FieldInfo, "__eq__", new=lambda *_: True)
@pytest.mark.parametrize(
    "prefix, delimiter, res",
    [
        ("", "__", {"a": None, "b__c": None, "b__d__e": None}),
        ("", "___", {"a": None, "b___c": None, "b___d___e": None}),
        ("f", "__", {"f__a": None, "f__b__c": None, "f__b__d__e": None}),
    ]
)
def test_squash_filter(prefix: str, delimiter: str, res: dict[str, Any]):
    assert squash_filter(
        filter_=FilterTest,
        prefix=prefix, 
        delimiter=delimiter,
    ) == res
   

@pytest.mark.parametrize(
    "prefix, delimiter, data, res",
    [
        ("", "__", {"a": 1}, {"a": 1}),
        ("f", "__", {"f__a": 1}, {"a": 1}),
        (
                "", "__",  
                {"a": 1, "b__c": 2, "b__d__e": 3},
                {"a": 1, 'b': {"c": 2, "d": {"e": 3}}},
        ),
        (
                "f", "__",
                {"f__a": 1, "f__b__c": 2, "f__b__d__e": 3},
                {"a": 1, 'b': {"c": 2, "d": {"e": 3}}},
        ),
    ]
)
def test_inflate_filter(prefix: str, delimiter: str, data: dict[str, Any], res: dict[str, Any]):
    assert inflate_filter(
        filter_=FilterTest,
        prefix=prefix, 
        delimiter=delimiter, 
        data=data,
    ).model_dump(exclude_unset=True) == res


def test_inflate_filter_ignores_none_and_unknown_values():
    result = inflate_filter(
        filter_=FilterTest,
        prefix="",
        delimiter="__",
        data={"a": None, "b__c": None, "unknown": 1},
    )

    assert result.model_dump(exclude_unset=True) == {}


def test_inflate_filter_does_not_confuse_overlapping_nested_names():
    class ShortNestedFilter(BaseFilter):
        value: int

    class LongNestedFilter(BaseFilter):
        value: int

    class OverlappingFilter(BaseFilter):
        b: ShortNestedFilter
        billing: LongNestedFilter

    result = inflate_filter(
        filter_=OverlappingFilter,
        prefix="",
        delimiter="__",
        data={"billing__value": 7},
    )

    assert result.model_dump(exclude_unset=True) == {"billing": {"value": 7}}


@pytest.mark.parametrize("prefix, delimiter", [("", "__"), ("api", "___")])
def test_squash_and_inflate_round_trip(prefix: str, delimiter: str):
    class SearchableNestedFilter(BaseFilter):
        value: int
        query: str = SearchField(target=["value"])

    class SearchableFilter(BaseFilter):
        identifier: int
        nested: SearchableNestedFilter

    flat_data = {
        add_prefix("identifier", prefix, delimiter): 1,
        add_prefix(f"nested{delimiter}value", prefix, delimiter): 2,
        add_prefix(f"nested{delimiter}query", prefix, delimiter): "needle",
    }
    squashed = squash_filter(SearchableFilter, prefix=prefix, delimiter=delimiter)
    inflated = inflate_filter(SearchableFilter, prefix=prefix, delimiter=delimiter, data=flat_data)

    assert set(squashed) == set(flat_data)
    assert inflated.model_dump(exclude_unset=True) == {
        "identifier": 1,
        "nested": {"value": 2, "query": "needle"},
    }

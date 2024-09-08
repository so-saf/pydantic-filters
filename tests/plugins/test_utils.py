from typing import Dict, Any
from unittest import mock

import pytest
from pydantic.fields import FieldInfo

from pydantic_filters import BaseFilter
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
def test_squash_filter(prefix: str, delimiter: str, res: Dict[str, Any]):
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
def test_inflate_filter(prefix: str, delimiter: str, data: Dict[str, Any], res: Dict[str, Any]):
    assert inflate_filter(
        filter_=FilterTest,
        prefix=prefix, 
        delimiter=delimiter, 
        data=data,
    ).model_dump(exclude_unset=True) == res

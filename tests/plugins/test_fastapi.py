from inspect import Parameter
from unittest import mock

import pytest
from pydantic import Field
from pydantic.fields import FieldInfo
from fastapi import Query
from fastapi import params as fastapi_params

from pydantic_filters import BaseFilter
from pydantic_filters.plugins.fastapi import (
    _field_info_to_query,
    _get_custom_params,
)
from tests.misc import __field_info_eq__


@pytest.mark.parametrize(
    "field_info, fastapi_query",
    [
        (Field(), Query()),
        (Field(le=1), Query(le=1)),
    ],
)
def test_field_info_to_query(field_info: FieldInfo, fastapi_query: fastapi_params.Query):
    assert __field_info_eq__(
        _field_info_to_query(field_info),
        fastapi_query,
    )
    
    
class DeepNestedFilter(BaseFilter):
    e: int


class NestedFilter(BaseFilter):
    c: int
    d: DeepNestedFilter


class FilterTest(BaseFilter):
    a: int
    b: NestedFilter


@mock.patch.object(fastapi_params.Query, "__eq__", new=__field_info_eq__)
def test_filter_to_function():
    assert _get_custom_params(filter_=FilterTest, prefix="", delimiter="__") == [
        Parameter(
            name="a",
            kind=Parameter.KEYWORD_ONLY,
            default=fastapi_params.Query(None),
            annotation=int,
        ),
        Parameter(
            name="b__c",
            kind=Parameter.KEYWORD_ONLY,
            default=fastapi_params.Query(None),
            annotation=int,
        ),
        Parameter(
            name="b__d__e",
            kind=Parameter.KEYWORD_ONLY,
            default=fastapi_params.Query(None),
            annotation=int,
        ),
    ]

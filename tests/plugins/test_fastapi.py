from inspect import Parameter, signature
from unittest import mock

import pytest
import httpx2
from fastapi import FastAPI
from pydantic import Field
from pydantic.fields import FieldInfo
from fastapi import Query
from fastapi import params as fastapi_params

from pydantic_filters import BaseFilter, BaseSort, FilterField, OffsetPagination
from pydantic_filters.plugins.fastapi import (
    FilterDepends,
    PaginationDepends,
    SortDepends,
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


def test_field_info_to_query_preserves_schema_and_alias_metadata():
    field_kwargs = dict(
        alias="public_name",
        title="Name",
        description="Public display name",
        examples=["Alice"],
        json_schema_extra={"x-field": "name"},
        min_length=2,
        max_length=20,
    )
    if hasattr(FieldInfo(), "deprecated"):
        field_kwargs["deprecated"] = True
    field_info = Field(**field_kwargs)

    query = _field_info_to_query(field_info)

    assert query.alias == "public_name"
    assert query.title == "Name"
    assert query.description == "Public display name"
    assert query.examples == ["Alice"]
    assert query.deprecated is getattr(field_info, "deprecated", None)
    assert query.json_schema_extra == {"x-field": "name"}
    assert query.metadata == field_info.metadata
    assert query.metadata is not field_info.metadata


def test_field_info_to_query_preserves_default_factory():
    factory = lambda: "generated"
    query = _field_info_to_query(Field(default_factory=factory))

    assert query.default_factory is factory
    
    
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


@pytest.mark.anyio
async def test_filter_depends_exposes_flat_signature_and_inflates_values():
    dependency = FilterDepends(FilterTest).dependency

    assert list(signature(dependency).parameters) == ["a", "b__c", "b__d__e"]
    result = await dependency(a=1, b__c=2, b__d__e=3)
    assert result.model_dump(exclude_unset=True) == {
        "a": 1,
        "b": {"c": 2, "d": {"e": 3}},
    }


@pytest.mark.parametrize(
    "factory, model, kwargs, expected",
    [
        (PaginationDepends, OffsetPagination, {"limit": 25, "offset": 50}, {"limit": 25, "offset": 50}),
        (SortDepends, BaseSort, {"sort_by": "name"}, {"sort_by": "name"}),
    ],
)
@pytest.mark.anyio
async def test_model_dependency_factories_construct_models(factory, model, kwargs, expected):
    dependency = factory(model).dependency

    assert set(signature(dependency).parameters) == set(model.model_fields)
    assert (await dependency(**kwargs)).model_dump(exclude_unset=True) == expected


@pytest.mark.anyio
async def test_filter_depends_parses_nested_query_parameters_end_to_end():
    app = FastAPI()

    @app.get("/")
    async def endpoint(filter_: FilterTest = FilterDepends(FilterTest)):
        return filter_.model_dump(exclude_unset=True)

    async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/",
            params={"a": "1", "b__c": "2", "b__d__e": "3"},
        )

    assert response.status_code == 200
    assert response.json() == {"a": 1, "b": {"c": 2, "d": {"e": 3}}}


@pytest.mark.anyio
async def test_filter_depends_supports_aliases_and_repeated_list_parameters():
    class ApiFilter(BaseFilter):
        identifiers: list[int]
        internal_name: str = FilterField(alias="name")

    app = FastAPI()

    @app.get("/")
    async def endpoint(filter_: ApiFilter = FilterDepends(ApiFilter)):
        return filter_.model_dump(exclude_unset=True)

    async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/",
            params=[("identifiers", "1"), ("identifiers", "2"), ("name", "Alice")],
        )

    assert response.status_code == 200
    assert response.json() == {"identifiers": [1, 2], "internal_name": "Alice"}


@pytest.mark.anyio
async def test_model_dependencies_apply_fastapi_defaults_and_validation():
    app = FastAPI()

    @app.get("/")
    async def endpoint(
            pagination: OffsetPagination = PaginationDepends(OffsetPagination),
            sort: BaseSort = SortDepends(BaseSort),
    ):
        return {"pagination": pagination.model_dump(), "sort": sort.model_dump()}

    async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url="http://test") as client:
        default_response = await client.get("/")
        invalid_response = await client.get("/", params={"limit": "0"})

    assert default_response.status_code == 200
    assert default_response.json() == {
        "pagination": {"limit": 100, "offset": 0},
        "sort": {"sort_by": None, "sort_by_order": "asc"},
    }
    assert invalid_response.status_code == 422

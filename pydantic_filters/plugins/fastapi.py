from copy import deepcopy
from inspect import Parameter, signature
from typing import Any, List, Tuple, Type, TypeVar

from fastapi import Depends, Query
from fastapi import params as fastapi_params
from pydantic.fields import FieldInfo

from pydantic_filters import BaseFilter, BasePagination, BaseSort

from ._utils import inflate_filter, squash_filter

_Filter = TypeVar("_Filter", bound=BaseFilter)
_Pagination = TypeVar("_Pagination", bound=BasePagination)
_Sort = TypeVar("_Sort", bound=BaseSort)


def _field_info_to_query(
        field_info: FieldInfo,
) -> fastapi_params.Query:
    q = Query(
        default=field_info.default,
        default_factory=field_info.default_factory,
        alias=field_info.alias,
        alias_priority=field_info.alias_priority,
        validation_alias=field_info.validation_alias,
        serialization_alias=field_info.serialization_alias,
        title=field_info.title,
        description=field_info.description,
        discriminator=field_info.discriminator,
        examples=field_info.examples,
        deprecated=field_info.deprecated,
        json_schema_extra=field_info.json_schema_extra,
    )
    q.metadata = deepcopy(field_info.metadata)
    return q


def _get_custom_params(
        filter_: Type[_Filter],
        prefix: str,
        delimiter: str,
) -> List[Parameter]:

    def _converter(f: FieldInfo) -> Tuple[FieldInfo, fastapi_params.Query]:
        return f, _field_info_to_query(f)

    squashed = squash_filter(
        filter_=filter_,
        prefix=prefix,
        delimiter=delimiter,
        converter=_converter,
    )

    return [
        Parameter(
            name=key,
            kind=Parameter.KEYWORD_ONLY,
            default=fastapi_query,
            annotation=field_info.annotation,
        )
        for key, (field_info, fastapi_query) in squashed.items()
    ]


def FilterDepends(  # noqa: N802
        filter_: Type[_Filter],
        prefix: str = "",
        delimiter: str = "__",
) -> _Filter:

    def _depends(**kwargs: Any) -> _Filter:  # noqa: ANN401
        """Signature of this function is replaced with Query parameters,
        and kwargs contains already valid data with
        our filters in the form of strings, which we collect into a filter object
        """
        return inflate_filter(
            filter_=filter_,
            prefix=prefix,
            delimiter=delimiter,
            data=kwargs,
        )

    # Переопределяем то, что функция принимает на вход
    _depends.__signature__ = signature(_depends).replace(
        parameters=_get_custom_params(filter_, prefix, delimiter),
    )

    return Depends(_depends)


def PaginationDepends(pagination: Type[_Pagination]) -> _Pagination:
    limit_field = pagination.model_fields["limit"]
    offset_field = pagination.model_fields["offset"]

    def _depends(
            limit: limit_field.annotation = _field_info_to_query(limit_field),
            offset: offset_field.annotation = _field_info_to_query(offset_field),
    ) -> _Filter:
        return pagination.model_construct(limit=limit, offset=offset)

    return Depends(_depends)


def SortDepends(sort: Type[_Sort]) -> _Sort:
    sort_by_field = sort.model_fields["sort_by"]
    sort_by_order_field = sort.model_fields["sort_by_order"]

    def _depends(
            sort_by: sort_by_field.annotation = _field_info_to_query(sort_by_field),
            sort_by_order: sort_by_order_field.annotation = _field_info_to_query(sort_by_order_field),
    ) -> _Sort:
        return sort.model_construct(sort_by=sort_by, sort_by_order=sort_by_order)

    return Depends(_depends)

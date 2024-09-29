from copy import deepcopy
from inspect import Parameter, signature
from typing import Any, List, Type, TypeVar

from fastapi import Depends, Query
from fastapi import params as fastapi_params
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from pydantic_filters import BaseFilter, BasePagination, BaseSort

from ._utils import inflate_filter, squash_filter

_Filter = TypeVar("_Filter", bound=BaseFilter)
_Pagination = TypeVar("_Pagination", bound=BasePagination)
_Sort = TypeVar("_Sort", bound=BaseSort)
_PydanticModel = TypeVar("_PydanticModel", bound=BaseModel)


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

    squashed = squash_filter(
        filter_=filter_,
        prefix=prefix,
        delimiter=delimiter,
    )

    return [
        Parameter(
            name=key,
            kind=Parameter.KEYWORD_ONLY,
            default=_field_info_to_query(field_info),
            annotation=field_info.annotation,
        )
        for key, field_info in squashed.items()
    ]


def FilterDepends(  # noqa: N802
        filter_: Type[_Filter],
        prefix: str = "",
        delimiter: str = "__",
) -> _Filter:  # pragma: no cover
    """
    Use this as fastapi.Depends, but for filters.

    Args:
        filter_: Filter class.
        prefix: key prefix.
        delimiter: Delimiter for prefix and nested models.
    """

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

    _depends.__signature__ = signature(_depends).replace(
        parameters=_get_custom_params(filter_, prefix, delimiter),
    )

    return Depends(_depends)


def _PydanticModelAsDepends(pydantic_model: Type[_PydanticModel]) -> _PydanticModel:  # pragma: no cover
    def _depends(**kwargs: Any) -> _Filter:  # noqa: ANN401
        return pydantic_model.model_construct(**kwargs)

    custom_params = []
    for key, field_info in pydantic_model.model_fields.items():

        custom_params.append(
            Parameter(
                name=key,
                kind=Parameter.KEYWORD_ONLY,
                default=_field_info_to_query(field_info),
                annotation=field_info.annotation,
            ),
        )

    _depends.__signature__ = signature(_depends).replace(
        parameters=custom_params,
    )

    return Depends(_depends)


def PaginationDepends(pagination: Type[_Pagination]) -> _Pagination:  # pragma: no cover
    """
    Use this as fastapi.Depends, but for pagination.

    Args:
        pagination: Pagination class
    """
    return _PydanticModelAsDepends(pagination)


def SortDepends(sort: Type[_Sort]) -> _Sort:  # pragma: no cover
    """
    Use this as fastapi.Depends, but for sort.

    Args:
        sort: Sort class.
    """
    return _PydanticModelAsDepends(sort)

from collections.abc import Callable
from types import UnionType
from typing import TYPE_CHECKING, Union, cast, get_args, get_origin

from pydantic.fields import Field, FieldInfo
from pydantic_core import PydanticUndefined, PydanticUndefinedType

from .._types import Annotation, NoneType
from ._fields import FilterFieldInfo, SearchFieldInfo

if TYPE_CHECKING:
    from ._base import BaseFilter
    from ._types import FilterType, SearchType


class NestedFilterExtractor:

    def __init__(self, optional: bool) -> None:
        self.optional = optional

    def __call__(
            self,
            field_name: str,  # noqa: ARG002
            field_info: FieldInfo,
            *,
            explicitly_required: bool = False,
    ) -> tuple[FieldInfo, type["BaseFilter"]]:
        if field_info.is_required():

            defaults_to_override = _get_defaults_dict_to_override(
                field_info,
                optional=self.optional,
                explicitly_required=explicitly_required,
            )

            return (
                FieldInfo.merge_field_infos(field_info, **defaults_to_override),
                cast("type[BaseFilter]", _simplify_optional_annotation(field_info.annotation)),
            )

        if isinstance(field_info.default, (FilterFieldInfo, SearchFieldInfo)):
            raise ValueError("Nested objects does not support FilterField, use pydantic.Field instead")

        return (
            field_info,
            cast("type[BaseFilter]", _simplify_optional_annotation(field_info.annotation)),
        )


class SearchFieldExtractor:

    def __init__(
            self,
            *,
            optional: bool,
            default_search_type: "SearchType",
            sequence_types: tuple[type, ...],
    ) -> None:
        self.optional = optional
        self.default_search_type = default_search_type
        self.sequence_types = sequence_types

    def __call__(
            self,
            field_name: str,  # noqa: ARG002
            field_info: FieldInfo,
            *,
            explicitly_required: bool = False,
    ) -> tuple[FieldInfo, "SearchFieldInfo"]:
        """Вытащить SearchFieldInfo из filed_info

        - SearchFieldInfo(type="like") -> FieldInfo(), SearchFieldInfo(type="like")
        """

        search_field: "SearchFieldInfo" = field_info.default
        if search_field.type is None:
            search_field.type = self.default_search_type

        search_field.is_sequence = _is_sequence(field_info.annotation, self.sequence_types)
        field_info_from_search: FieldInfo = Field(**search_field.field_kwargs)
        defaults_to_override = _get_defaults_dict_to_override(
            field_info_from_search,
            optional=self.optional,
            explicitly_required=explicitly_required,
        )

        return (
            FieldInfo.merge_field_infos(
                field_info,
                field_info_from_search,
                **defaults_to_override,
            ),
            search_field,
        )


class FilterFieldExtractor:

    def __init__(
            self,
            *,
            optional: bool,
            default_filter_type: "FilterType",
            sequence_types: tuple[type, ...],
            type_definer: Callable[[str], tuple[str, "FilterType"]],
    ) -> None:
        self.optional = optional
        self.default_filter_type = default_filter_type
        self.sequence_types = sequence_types
        self.type_definer = type_definer

    def __call__(
            self,
            field_name: str,
            field_info: FieldInfo,
            *,
            explicitly_required: bool = False,
    ) -> tuple[FieldInfo, FilterFieldInfo]:
        """Extract `FilterInfo` from `filed_info`"""

        # when `a: int` or `a: int = 5`
        if not isinstance(field_info.default, FilterFieldInfo):
            defaults_dict_to_override = _get_defaults_dict_to_override(
                field_info,
                optional=self.optional,
                explicitly_required=explicitly_required,
            )
            computed_name, computed_type = self.type_definer(field_name)

            return (
                FieldInfo.merge_field_infos(
                    field_info,
                    **defaults_dict_to_override,
                ),
                FilterFieldInfo(
                    target=computed_name,
                    type_=computed_type,
                    is_sequence=_is_sequence(field_info.annotation, self.sequence_types),
                ),
            )

        # when `a: int = FilterField(...)`

        filter_field: FilterFieldInfo = field_info.default
        computed_name, computed_filter_type = self.type_definer(field_name)

        if filter_field.target is None and filter_field.type is None:
            filter_field.target = computed_name
            filter_field.type = computed_filter_type
        elif filter_field.target is None and filter_field.type is not None:
            filter_field.target = field_name
        elif filter_field.target is not None and filter_field.type is None:
            filter_field.type = self.default_filter_type

        field_info_from_filter: FieldInfo = Field(**filter_field.field_kwargs)
        filter_field.is_sequence = _is_sequence(field_info.annotation, sequence_types=self.sequence_types)
        defaults_dict_to_override = _get_defaults_dict_to_override(
            field_info_from_filter,
            optional=self.optional,
            explicitly_required=explicitly_required,
        )

        return (
            FieldInfo.merge_field_infos(
                field_info,
                field_info_from_filter,
                **defaults_dict_to_override,
            ),
            filter_field,
        )


def is_filter_subclass(type_: Annotation) -> bool:
    from pydantic_filters.filter._base import BaseFilter  # noqa: PLC0415
    try:
        return issubclass(type_, BaseFilter)
    except TypeError:
        return False


def _is_sequence(
        annotation: Annotation,
        sequence_types: tuple[type, ...],
) -> bool:
    """
    str -> False
    list[str] -> True
    str | None -> False
    list[str] | None -> True
    list[str] | None -> True
    list[str] | str | None -> False
    """
    origin = get_origin(_simplify_optional_annotation(annotation))
    if origin in sequence_types:
        return True

    return False


def _simplify_optional_annotation(annotation: Annotation) -> Annotation:
    """
    str | None -> str
    list[str] | None -> list[str]
    int | str | None -> int | str | None
    str -> str
    """
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        args = set(get_args(annotation))
        args.discard(NoneType)
        if len(args) == 1:
            return args.pop()

    return annotation


def _get_defaults_dict_to_override(
        field_info: FieldInfo,
        *,
        optional: bool,
        explicitly_required: bool = False,
) -> dict[str, PydanticUndefinedType | None]:

    is_required = field_info.is_required()

    if explicitly_required:
        return {"default": PydanticUndefined}
    if not is_required:
        return {}
    if optional:
        return {"default": None}
    return {"default": PydanticUndefined}

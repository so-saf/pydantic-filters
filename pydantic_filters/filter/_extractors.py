from typing import TYPE_CHECKING, Callable, Dict, Optional, Tuple, Type, Union, cast, get_args, get_origin

from pydantic.fields import Field, FieldInfo
from pydantic_core import PydanticUndefined

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
    ) -> Tuple[FieldInfo, Type["BaseFilter"]]:
        if field_info.is_required():

            defaults_to_override = _get_defaults_dict_to_override(field_info, optional=self.optional)

            return (
                FieldInfo.merge_field_infos(field_info, **defaults_to_override),
                cast(Type["BaseFilter"], _simplify_optional_annotation(field_info.annotation)),
            )

        if isinstance(field_info.default, (FilterFieldInfo, SearchFieldInfo)):
            raise ValueError("Nested objects does not support FilterField, use pydantic.Field instead")

        return (
            field_info,
            cast(Type["BaseFilter"], _simplify_optional_annotation(field_info.annotation)),
        )


class SearchFieldExtractor:

    def __init__(
            self,
            *,
            optional: bool,
            default_search_type: "SearchType",
            sequence_types: Tuple[Type, ...],
    ) -> None:
        self.optional = optional
        self.default_search_type = default_search_type
        self.sequence_types = sequence_types

    def __call__(
            self,
            field_name: str,  # noqa: ARG002
            field_info: FieldInfo,
    ) -> Tuple[FieldInfo, "SearchFieldInfo"]:
        """Вытащить SearchFieldInfo из filed_info

        - SearchFieldInfo(type="like") -> FieldInfo(), SearchFieldInfo(type="like")
        """

        search_field: "SearchFieldInfo" = field_info.default
        if search_field.type is None:
            search_field.type = self.default_search_type

        search_field.is_sequence = _is_sequence(field_info.annotation, self.sequence_types)
        field_info_from_search: FieldInfo = Field(**search_field.field_kwargs)
        defaults_to_override = _get_defaults_dict_to_override(field_info_from_search, optional=self.optional)

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
            sequence_types: Tuple[Type, ...],
            type_definer: Callable[[str], Tuple[str, "FilterType"]],
    ) -> None:
        self.optional = optional
        self.default_filter_type = default_filter_type
        self.sequence_types = sequence_types
        self.type_definer = type_definer

    def __call__(
            self,
            field_name: str,
            field_info: FieldInfo,
    ) -> Tuple[FieldInfo, FilterFieldInfo]:
        """Extract `FilterInfo` from `filed_info`"""

        # when `a: int` or `a: int = 5`
        if not isinstance(field_info.default, FilterFieldInfo):
            defaults_dict_to_override = _get_defaults_dict_to_override(field_info, optional=self.optional)
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
        defaults_dict_to_override = _get_defaults_dict_to_override(field_info_from_filter, optional=self.optional)

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
        sequence_types: Tuple[Type, ...],
) -> bool:
    """
    str -> False
    List[str] -> True
    Optional[str] -> False
    Optional[List[str]] -> True
    Union[List[str], None] -> True
    Union[List[str], str, None] -> False
    """
    origin = get_origin(_simplify_optional_annotation(annotation))
    if origin in sequence_types:
        return True

    return False


def _simplify_optional_annotation(annotation: Annotation) -> Annotation:
    """
    Optional[str] -> str
    Optional[List[str]] -> List[str]
    Union[int, str, None] -> Union[int, str, None]
    str -> str
    """
    origin = get_origin(annotation)
    if origin is Union:
        args = set(get_args(annotation))
        args.discard(NoneType)
        if len(args) == 1:
            return args.pop()

    return annotation


def _get_defaults_dict_to_override(
        field_info: FieldInfo,
        *,
        optional: bool,
) -> Dict[str, Optional[type(PydanticUndefined)]]:

    is_required = field_info.is_required()
    is_ellipsis = field_info._attributes_set.get("default") is Ellipsis

    if is_ellipsis:
        return {"default": PydanticUndefined}
    elif not is_required:
        return {}
    elif is_required and optional:
        return {"default": None}
    elif is_required and not optional:
        return {"default": PydanticUndefined}

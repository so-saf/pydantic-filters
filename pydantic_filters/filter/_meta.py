from typing import TYPE_CHECKING, Any, Dict, Tuple, Type, cast

from pydantic._internal._model_construction import ModelMetaclass  # noqa: PLC2701

from ._definer import FilterTypeDefiner
from ._extractors import (
    FilterFieldExtractor,
    NestedFilterExtractor,
    SearchFieldExtractor,
    is_filter_subclass,
)
from ._fields import SearchFieldInfo

if TYPE_CHECKING:
    from ._base import BaseFilter
    from ._config import FilterConfigDict


class FilterMetaclass(ModelMetaclass):

    def __new__(
            cls,
            name: str,
            bases: Tuple[Type[Any], ...],
            namespace: Dict[str, Any],
            **kwargs: Any,  # noqa: ANN401
    ) -> Type["BaseFilter"]:
        return cls.__new(name, bases, namespace, **kwargs)

    @classmethod
    def __new(
            cls,
            name: str,
            bases: Tuple[Type[Any], ...],
            namespace: Dict[str, Any],
            **kwargs: Any,  # noqa: ANN401
    ) -> Type["BaseFilter"]:
        filter_class = cast(Type["BaseFilter"], super().__new__(cls, name, bases, namespace, **kwargs))
        model_config: FilterConfigDict = filter_class.model_config

        nested_field_extractor = NestedFilterExtractor(
            optional=model_config["optional"],
        )
        search_field_extractor = SearchFieldExtractor(
            optional=model_config["optional"],
            default_search_type=model_config["default_search_type"],
            sequence_types=model_config["sequence_types"],
        )
        filter_field_extractor = FilterFieldExtractor(
            optional=model_config["optional"],
            default_filter_type=model_config["default_filter_type"],
            sequence_types=model_config["sequence_types"],
            type_definer=FilterTypeDefiner(
                delimiter=model_config["delimiter"],
                default=model_config["default_filter_type"],
                suffixes_map=model_config["suffixes_map"],
            ),
        )

        annotations = namespace.get("__annotations__", {})
        filter_fields = {}
        search_fields = {}
        nested_fields = {}

        for field_name, field_info in filter_class.model_fields.items():
            if field_name not in annotations:
                continue

            # when `a: NestedFilter` or `a: NestedFilter = NestedFilter(...)`
            if is_filter_subclass(field_info.annotation):
                new_model_field, __nested_filter = nested_field_extractor(field_name, field_info)
                namespace[field_name] = new_model_field
                nested_fields[field_name] = __nested_filter
                continue

            # when `a: str = SearchField(...)`
            elif isinstance(field_info.default, SearchFieldInfo):
                new_model_field, __search_field = search_field_extractor(field_name, field_info)
                namespace[field_name] = new_model_field
                search_fields[field_name] = __search_field
                continue

            # Declared either with FilterField or without using custom fields at all
            new_model_field, filter_field = filter_field_extractor(field_name, field_info)
            namespace[field_name] = new_model_field
            filter_fields[field_name] = filter_field

        recreated_filter_class = cast(Type["BaseFilter"], super().__new__(cls, name, bases, namespace, **kwargs))
        # Assigning a new value
        # It is the override that is used, the update method will update the parent field,
        # which will result in a common field for all inheritors of the BaseFilter class, which must be avoided
        recreated_filter_class.filter_fields = {**filter_class.filter_fields, **filter_fields}
        recreated_filter_class.search_fields = {**filter_class.search_fields, **search_fields}
        recreated_filter_class.nested_filters = {**filter_class.nested_filters, **nested_fields}

        return recreated_filter_class

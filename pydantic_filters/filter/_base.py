from typing import TYPE_CHECKING, ClassVar, Dict, Type

from pydantic import BaseModel

from ._config import FilterConfigDict
from ._meta import FilterMetaclass
from ._types import FilterType, SearchType, get_suffixes_map

if TYPE_CHECKING:
    from ._fields import FilterFieldInfo, SearchFieldInfo


class BaseFilter(BaseModel, metaclass=FilterMetaclass):
    """
    A base class for creating pydantic-based filters.
    """

    if TYPE_CHECKING:
        filter_fields: ClassVar[Dict[str, "FilterFieldInfo"]]
        """
        Metadata about the filters fields defined on the model,
        mapping of field names to [`FilterFieldInfo`][pydantic_filters.filter._fields.FilterFieldInfo] objects.
        """

        search_fields: ClassVar[Dict[str, "SearchFieldInfo"]]
        """
        Metadata about the search fields defined on the model,
        mapping of field names to [`SearchFieldInfo`][pydantic_filters.filter._fields.SearchFieldInfo] objects.
        """

        nested_filters: ClassVar[Dict[str, Type["BaseFilter"]]]
        """
        Metadata about the nested filters defined on the model,
        mapping of field names to [`BaseFilter`][pydantic_filters.filter._base.BaseFilter] objects.
        """
    else:
        filter_fields: ClassVar = {}
        search_fields: ClassVar = {}
        nested_filters: ClassVar = {}

    model_config = FilterConfigDict(
        delimiter="__",
        optional=True,
        default_filter_type=FilterType.eq,
        default_search_type=SearchType.case_insensitive,
        suffixes_map=get_suffixes_map(),
        sequence_types=(list, set),
    )
    """
    Configuration for the model, should be a dictionary conforming to
    [`FilterConfigDict`][pydantic_filters.filter._config.FilterConfigDict].
    """

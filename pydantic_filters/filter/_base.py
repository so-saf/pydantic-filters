from typing import TYPE_CHECKING, ClassVar, Dict, Type

from pydantic import BaseModel

from ._config import FilterConfigDict
from ._meta import FilterMetaclass
from ._types import FilterType, SearchType, get_suffixes_map

if TYPE_CHECKING:
    from ._fields import FilterFieldInfo, SearchFieldInfo


class BaseFilter(BaseModel, metaclass=FilterMetaclass):

    if TYPE_CHECKING:
        filter_fields: ClassVar[Dict[str, "FilterFieldInfo"]]
        search_fields: ClassVar[Dict[str, "SearchFieldInfo"]]
        nested_filters: ClassVar[Dict[str, Type["BaseFilter"]]]
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

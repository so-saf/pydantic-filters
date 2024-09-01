from typing import Dict, Tuple, Type

from pydantic import ConfigDict

from ._types import FilterType, SearchType


class FilterConfigDict(ConfigDict, total=False):
    delimiter: str
    optional: bool
    default_filter_type: FilterType
    default_search_type: SearchType
    suffixes_map: Dict[str, FilterType]
    sequence_types: Tuple[Type, ...]

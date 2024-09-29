from typing import Dict, Tuple, Type

from pydantic import ConfigDict

from ._types import FilterType, SearchType


class FilterConfigDict(ConfigDict, total=False):
    """A TypedDict for configuring filtering"""

    delimiter: str
    """A delimiter before the suffix."""

    optional: bool
    """Make all fields optional"""

    default_filter_type: FilterType
    """
    Default filter type if not specified directly in
    [`FilterField`][pydantic_filters.filter._fields.FilterField]
    or by suffix.
    """

    default_search_type: SearchType
    """
    Default search type if not specified directly in
    [`SearchField`][pydantic_filters.filter._fields.SearchField].
    """

    suffixes_map: Dict[str, FilterType]
    """Suffix mapping to filter type"""

    sequence_types: Tuple[Type, ...]
    """Types that are considered sequences"""

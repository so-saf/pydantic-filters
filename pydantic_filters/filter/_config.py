from pydantic import ConfigDict

from ._types import FilterType, SearchType


class FilterConfigDict(ConfigDict, total=False):
    """A TypedDict for configuring filtering."""

    delimiter: str
    """A delimiter before the suffix."""

    optional: bool
    """Make otherwise-required fields optional."""

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

    suffixes_map: dict[str, FilterType]
    """Mapping of recognized suffixes to filter types."""

    sequence_types: tuple[type, ...]
    """Annotation origins that are considered sequences."""

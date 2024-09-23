from itertools import chain
from typing import TYPE_CHECKING, Any, Dict, Type, TypeVar

from pydantic_filters.filter._base import BaseFilter

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo

_T = TypeVar("_T")
_Filter = TypeVar("_Filter", bound=BaseFilter)


def add_prefix(item: str, prefix: str, delimiter: str) -> str:
    if not prefix:
        return item

    return prefix + delimiter + item


def remove_prefix(item: str, prefix: str, delimiter: str) -> str:
    if not prefix:
        return item

    if item.startswith(prefix + delimiter):
        return item[len(prefix) + len(delimiter):]

    return item


def squash_filter(
        filter_: Type[_Filter],
        prefix: str,
        delimiter: str,
) -> Dict[str, "FieldInfo"]:
    """
    **Example:**

    >>> class DeepNestedFilter(BaseFilter):
    ...    e: int
    >>> class NestedFilter(BaseFilter):
    ...    c: int
    ...    d: DeepNestedFilter
    >>> class MyFilter(BaseFilter):
    ...    a: int
    ...    b: NestedFilter
    >>> squash_filter(MyFilter, "", "__")
    {"a": ..., "b__c": ..., "b__d__e": ...}
    """

    squashed = {}

    for key in chain(filter_.filter_fields, filter_.search_fields):
        field_info = filter_.model_fields[key]
        squashed[add_prefix(key, prefix, delimiter)] = field_info

    for key, nested_filter in filter_.nested_filters.items():
        squashed.update(
            squash_filter(
                filter_=nested_filter,
                prefix=add_prefix(key, prefix, delimiter),
                delimiter=delimiter,
            ),
        )

    return squashed


def inflate_filter(
        filter_: Type[_Filter],
        prefix: str,
        delimiter: str,
        data: Dict[str, Any],
) -> _Filter:
    """
    **Example:**

    >>> class DeepNestedFilter(BaseFilter):
    ...    e: int
    >>> class NestedFilter(BaseFilter):
    ...    c: int
    ...    d: DeepNestedFilter
    >>> class MyFilter(BaseFilter):
    ...    a: int
    ...    b: NestedFilter
    >>> inflate_filter(MyFilter, "", "__", {"a": 1, "b__c": 2, "b__d__e": 3})
    MyFilter(a=1, b=NestedFilter(c=2, d=DeepNestedFilter(e=3)))
    """

    to_construct: Dict[str, Any] = {}
    nested_kwargs: Dict[str, Any] = {}
    for k, v in data.items():
        if v is None:
            continue

        k_without_prefix = remove_prefix(k, prefix, delimiter)
        if k_without_prefix in filter_.filter_fields.keys() | filter_.search_fields.keys():
            to_construct[k_without_prefix] = v
        else:
            nested_kwargs[k_without_prefix] = v

    for field_name, nested_filter in filter_.nested_filters.items():
        nested = inflate_filter(
            filter_=nested_filter,
            prefix=field_name,
            delimiter=delimiter,
            data={
                k: v
                for k, v in nested_kwargs.items()
                if k.startswith(field_name)
            },
        )

        # skip if nested data is empty
        if not nested.model_dump(exclude_unset=True):
            continue

        to_construct[field_name] = nested

    return filter_.model_construct(**to_construct)

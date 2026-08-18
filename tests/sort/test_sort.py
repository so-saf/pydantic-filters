import pytest
from pydantic import ValidationError

from pydantic_filters import BaseSort, SortByOrder


def test_sort_defaults() -> None:
    sort = BaseSort()

    assert sort.sort_by is None
    assert sort.sort_by_order is SortByOrder.asc
    assert sort.model_dump() == {"sort_by": None, "sort_by_order": SortByOrder.asc}


@pytest.mark.parametrize("value", [SortByOrder.asc, SortByOrder.desc, "asc", "desc"])
def test_sort_accepts_enum_and_string_orders(value) -> None:
    assert BaseSort(sort_by="name", sort_by_order=value).sort_by_order is SortByOrder(value)


def test_sort_rejects_unknown_order() -> None:
    with pytest.raises(ValidationError, match="sort_by_order"):
        BaseSort(sort_by="name", sort_by_order="random")

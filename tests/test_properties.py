from hypothesis import given
from hypothesis import strategies as st

from pydantic_filters import BaseFilter
from pydantic_filters.filter._definer import FilterTypeDefiner
from pydantic_filters.filter._types import FilterType
from pydantic_filters.plugins._utils import add_prefix, inflate_filter, remove_prefix, squash_filter


safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=0,
    max_size=30,
)


@given(item=safe_text, prefix=safe_text, delimiter=st.sampled_from(["__", "___", "::"]))
def test_add_and_remove_prefix_round_trip(item: str, prefix: str, delimiter: str) -> None:
    assert remove_prefix(add_prefix(item, prefix, delimiter), prefix, delimiter) == item


@given(page=st.integers(min_value=1, max_value=10_000), per_page=st.integers(min_value=1, max_value=10_000))
def test_page_offset_formula_is_never_negative(page: int, per_page: int) -> None:
    from pydantic_filters import PagePagination

    pagination = PagePagination(page=page, per_page=per_page)
    assert pagination.get_offset() == (page - 1) * per_page
    assert pagination.get_offset() >= 0


@given(target=safe_text.filter(lambda value: "__" not in value))
def test_filter_type_definer_keeps_targets_without_known_suffix(target: str) -> None:
    definer = FilterTypeDefiner("__", FilterType.eq, {"lt": FilterType.lt})
    assert definer(target) == (target, FilterType.eq)


class PropertyNestedFilter(BaseFilter):
    values: list[int]


class PropertyFilter(BaseFilter):
    identifier: int
    nested: PropertyNestedFilter


@given(
    identifier=st.integers(),
    values=st.lists(st.integers(), max_size=20),
    prefix=st.sampled_from(["", "api", "filters"]),
    delimiter=st.sampled_from(["__", "___"]),
)
def test_squash_inflate_round_trip_for_generated_values(
        identifier: int,
        values: list[int],
        prefix: str,
        delimiter: str,
) -> None:
    flat_data = {
        add_prefix("identifier", prefix, delimiter): identifier,
        add_prefix(f"nested{delimiter}values", prefix, delimiter): values,
    }

    assert set(squash_filter(PropertyFilter, prefix, delimiter)) == set(flat_data)
    assert inflate_filter(PropertyFilter, prefix, delimiter, flat_data).model_dump(exclude_unset=True) == {
        "identifier": identifier,
        "nested": {"values": values},
    }

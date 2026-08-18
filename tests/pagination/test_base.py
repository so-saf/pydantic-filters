import pytest
from pydantic import ValidationError

from pydantic_filters.pagination import BasePagination, PagePagination, OffsetPagination


class TestOffsetPagination:

    def test_defaults(self) -> None:
        pagination = OffsetPagination()
        assert pagination.get_limit() == 100
        assert pagination.get_offset() == 0
    
    @pytest.mark.parametrize(
        "obj, limit, offset",
        [
            (OffsetPagination(limit=1, offset=1), 1, 1),
            (OffsetPagination(limit=10, offset=0), 10, 0),
        ]
    )
    def test_get_limit_get_offset(self, obj: BasePagination, limit: int, offset: int) -> None:
        assert obj.get_limit() == limit
        assert obj.get_offset() == offset


class TestPagePagination:

    def test_defaults(self) -> None:
        pagination = PagePagination()
        assert pagination.get_limit() == 100
        assert pagination.get_offset() == 0

    @pytest.mark.parametrize(
        "obj, limit, offset",
        [
            (PagePagination(page=1, per_page=10), 10, 0),
            (PagePagination(page=12, per_page=34), 34, 374),
        ]
    )
    def test_get_limit_get_offset(self, obj: BasePagination, limit: int, offset: int) -> None:
        assert obj.get_limit() == limit
        assert obj.get_offset() == offset


@pytest.mark.parametrize(
    "pagination, kwargs, field",
    [
        (OffsetPagination, {"limit": 0}, "limit"),
        (OffsetPagination, {"offset": -1}, "offset"),
        (PagePagination, {"page": 0}, "page"),
        (PagePagination, {"per_page": 0}, "per_page"),
    ],
)
def test_pagination_rejects_values_below_minimum(pagination, kwargs, field) -> None:
    with pytest.raises(ValidationError, match=field):
        pagination(**kwargs)

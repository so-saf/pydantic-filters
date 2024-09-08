import pytest

from pydantic_filters.pagination import PaginationInterface, PagePagination, OffsetPagination


class TestOffsetPagination:
    
    @pytest.mark.parametrize(
        "obj, limit, offset",
        [
            (OffsetPagination(limit=1, offset=1), 1, 1),
            (OffsetPagination(limit=10, offset=0), 10, 0),
        ]
    )
    def test_get_limit_get_offset(self, obj: PaginationInterface, limit: int, offset: int) -> None:
        assert obj.get_limit() == limit
        assert obj.get_offset() == offset


class TestPagePagination:

    @pytest.mark.parametrize(
        "obj, limit, offset",
        [
            (PagePagination(page=1, per_page=10), 10, 0),
            (PagePagination(page=12, per_page=34), 34, 374),
        ]
    )
    def test_get_limit_get_offset(self, obj: PaginationInterface, limit: int, offset: int) -> None:
        assert obj.get_limit() == limit
        assert obj.get_offset() == offset

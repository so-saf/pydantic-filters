# Pagination

Pagination models expose a limit and an offset through `get_limit()` and
`get_offset()`. The SQLAlchemy driver uses those values to apply `LIMIT` and
`OFFSET`.

## Limit and offset

[`OffsetPagination`][pydantic_filters.OffsetPagination] defaults to 100 items
from the beginning of the result set:

```python
from pydantic_filters import OffsetPagination


pagination = OffsetPagination(limit=25, offset=50)

assert pagination.get_limit() == 25
assert pagination.get_offset() == 50
```

`limit` must be at least 1 and `offset` must be non-negative.

## Page and page size

[`PagePagination`][pydantic_filters.PagePagination] converts a one-based page
number into an offset:

```python
from pydantic_filters import PagePagination


pagination = PagePagination(page=3, per_page=25)

assert pagination.get_limit() == 25
assert pagination.get_offset() == 50
```

Both `page` and `per_page` must be at least 1. Their defaults are `1` and `100`.

## Custom pagination

Inherit from [`BasePagination`][pydantic_filters.BasePagination], add any fields
your API needs, and implement both methods:

```python
from pydantic import Field
from pydantic_filters import BasePagination


class CursorWindow(BasePagination):
    start: int = Field(0, ge=0)
    size: int = Field(50, ge=1, le=500)

    def get_limit(self) -> int:
        return self.size

    def get_offset(self) -> int:
        return self.start
```

See the [SQLAlchemy guide](sqlalchemy.md#pagination) for statement integration
and the [FastAPI guide](fastapi.md#pagination-and-sorting) for query parameters.

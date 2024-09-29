
Pagination allows you to do batch selection of data from their source.
The library provides two ready-to-use classes for that:

- [`OfsettPagination`][pydantic_filters.OffsetPagination]
- [`PagePagination`][pydantic_filters.PagePagination]

## Custom Pagination

The custom pagination class should:

- Inherit from the [`BasePagination`][pydantic_filters.BasePagination] class.
- Implement the [`get_offset`][pydantic_filters.BasePagination.get_offset] and
[`get_limit`][pydantic_filters.BasePagination.get_limit] methods.

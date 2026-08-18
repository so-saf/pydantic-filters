# FastAPI

The FastAPI plugin turns model fields into validated query parameters:

- [`FilterDepends`][pydantic_filters.plugins.fastapi.FilterDepends] flattens
  filters, including nested filters;
- [`PaginationDepends`][pydantic_filters.plugins.fastapi.PaginationDepends]
  exposes a pagination model;
- [`SortDepends`][pydantic_filters.plugins.fastapi.SortDepends] exposes a sort
  model.

Install FastAPI separately because it is not a required package dependency:

```shell
pip install "pydantic-filters" "fastapi>=0.100"
```

## Filters

```python
from typing import Annotated

from fastapi import FastAPI

from pydantic_filters import BaseFilter, FilterField, SearchField
from pydantic_filters.plugins.fastapi import FilterDepends


class DepartmentFilter(BaseFilter):
    manager_id: list[int]


class UserFilter(BaseFilter):
    login: list[str]
    age__lt: int = FilterField(gt=0, le=150)
    q: str = SearchField(target=["login", "full_name", "email"])
    department: DepartmentFilter


app = FastAPI()


@app.get("/users")
async def get_users(
    filter_: Annotated[UserFilter, FilterDepends(UserFilter)],
):
    return filter_.model_dump(exclude_unset=True)
```

The endpoint accepts flat query parameters such as:

```text
/users?login=alice&login=bob&age__lt=40&department__manager_id=5
```

and constructs the equivalent nested model:

```python
UserFilter(
    login=["alice", "bob"],
    age__lt=40,
    department=DepartmentFilter(manager_id=[5]),
)
```

`FilterDepends` preserves Pydantic validation constraints and schema metadata,
including aliases, descriptions, examples, and deprecation flags. Repeated query
parameters are parsed into sequence fields.

### Prefix and delimiter

Use `prefix` when embedding the whole filter under a query-parameter namespace.
Use `delimiter` to control how nested names are flattened:

```python
filter_: Annotated[
    UserFilter,
    FilterDepends(UserFilter, prefix="filter", delimiter="__"),
]
```

The resulting names begin with `filter__`, for example
`filter__department__manager_id`.

## Pagination and sorting

```python
from enum import Enum
from typing import Annotated

from pydantic_filters import BaseSort, OffsetPagination
from pydantic_filters.plugins.fastapi import PaginationDepends, SortDepends


class UserSortField(str, Enum):
    id = "id"
    login = "login"
    age = "age"


class UserSort(BaseSort):
    sort_by: UserSortField | None = None


@app.get("/users/page")
async def get_user_page(
    pagination: Annotated[
        OffsetPagination,
        PaginationDepends(OffsetPagination),
    ],
    sort: Annotated[UserSort, SortDepends(UserSort)],
):
    return {"pagination": pagination, "sort": sort}
```

This exposes `limit`, `offset`, `sort_by`, and `sort_by_order` as query
parameters and applies the models' defaults and validation rules.

!!! tip

    FastAPI 0.115 and newer supports Pydantic query-parameter models directly.
    For non-nested pagination and sort models, `Annotated[Model, Query()]` can
    replace `PaginationDepends` or `SortDepends`. `FilterDepends` remains useful
    for flattening nested filter models.

# Sorting

[`BaseSort`][pydantic_filters.BaseSort] contains two fields:

- `sort_by`: the target field name, or `None` to leave the statement unchanged;
- `sort_by_order`: `asc` by default, or `desc`.

```python
from pydantic_filters import BaseSort, SortByOrder


sort = BaseSort(sort_by="created_at", sort_by_order=SortByOrder.desc)
```

For a public API, restrict `sort_by` to known values with an enum. This makes
invalid values fail Pydantic validation before they reach the driver:

```python
from enum import Enum

from pydantic_filters import BaseSort


class UserSortField(str, Enum):
    id = "id"
    login = "login"
    full_name = "full_name"


class UserSort(BaseSort):
    sort_by: UserSortField | None = None
```

The SQLAlchemy driver raises
[`AttributeNotFoundSaDriverError`][pydantic_filters.drivers.sqlalchemy.AttributeNotFoundSaDriverError]
if `sort_by` does not name an attribute on the model. See the
[SQLAlchemy guide](sqlalchemy.md#sorting) for applying a sort model to a statement.

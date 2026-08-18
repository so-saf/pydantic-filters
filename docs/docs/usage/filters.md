# Filters

[`BaseFilter`][pydantic_filters.BaseFilter] is a Pydantic model that also stores
the metadata a driver needs to build a query. Define normal typed fields and
instantiate the filter with values supplied by your application.

```python
from pydantic_filters import BaseFilter, SearchField


class UserFilter(BaseFilter):
    login: list[str]
    login__n: list[str]
    age__ge: int
    age__lt: int
    department_id: list[int]
    q: str = SearchField(target=["login", "full_name", "email"])
```

By default, declared fields are not required. Consequently, `UserFilter()` is
valid and a driver ignores every field that was not explicitly supplied:

```python
filter_ = UserFilter(department_id=[3, 4], age__ge=18)

assert filter_.model_dump(exclude_unset=True) == {
    "department_id": [3, 4],
    "age__ge": 18,
}
```

To make one field required, use an ellipsis. To make every field follow normal
Pydantic required-field semantics, set `optional=False` in `model_config`.

```python
class RequiredFilter(BaseFilter):
    model_config = {**BaseFilter.model_config, "optional": False}

    tenant_id: int


class PartlyRequiredFilter(BaseFilter):
    tenant_id: int = ...
    name: str
```

## Operators and suffixes

A field suffix determines its operation. With the default `__` delimiter, the
built-in suffixes are:

| Operation | Suffixes | Scalar SQL | Sequence SQL |
| --- | --- | --- | --- |
| Equal | `eq` or no suffix | `column = value` | `column IN (...)` |
| Not equal | `n`, `ne`, `neq` | `column != value` | `column NOT IN (...)` |
| Is null | `null`, `isnull` | `IS NULL` when true, otherwise `IS NOT NULL` | — |
| Greater than | `gt` | `column > value` | conditions joined with `OR` |
| Greater than or equal | `ge`, `gte` | `column >= value` | conditions joined with `OR` |
| Less than | `lt` | `column < value` | conditions joined with `OR` |
| Less than or equal | `le`, `lte` | `column <= value` | conditions joined with `OR` |
| `LIKE` | `l`, `like` | `column LIKE value` | conditions joined with `OR` |
| `ILIKE` | `il`, `ilike` | `column ILIKE value` | conditions joined with `OR` |

For example:

```python
class ProductFilter(BaseFilter):
    id: list[int]            # id IN (...)
    id__n: list[int]         # id NOT IN (...)
    price__gte: int          # price >= value
    price__lt: int           # price < value
    archived_at__null: bool  # archived_at IS NULL / IS NOT NULL
```

The complete operation enum is [`FilterType`][pydantic_filters.FilterType].
An unknown suffix is treated as part of the target name and uses
`default_filter_type`.

!!! note

    The table describes the bundled SQLAlchemy driver. A different driver may
    translate the same filter metadata differently.

## Search fields

[`SearchField`][pydantic_filters.SearchField] applies one value to several
targets and combines the target conditions with `OR`:

```python
from pydantic_filters import BaseFilter, SearchField, SearchType


class UserFilter(BaseFilter):
    q: str = SearchField(
        target=["login", "full_name", "email"],
        type_=SearchType.case_insensitive,
    )
```

For the SQLAlchemy driver, `UserFilter(q="alice")` produces a case-insensitive
substring search equivalent to:

```sql
login ILIKE '%alice%' OR full_name ILIKE '%alice%' OR email ILIKE '%alice%'
```

Use `SearchType.case_sensitive` for `LIKE`. A sequence-typed search field also
combines its values with `OR`.

## Nested filters

A field annotated with another `BaseFilter` is a nested filter:

```python
class DepartmentFilter(BaseFilter):
    manager_id: list[int]


class UserFilter(BaseFilter):
    login: list[str]
    department: DepartmentFilter


filter_ = UserFilter(
    login=["alice", "bob"],
    department=DepartmentFilter(manager_id=[5]),
)
```

The SQLAlchemy driver expects the nested field name (`department`) to match a
relationship on the current model. It adds the necessary joins and supports
multiple nesting levels, self-referential relationships, many-to-many
relationships, and composite foreign keys. See the [SQLAlchemy guide](sqlalchemy.md).

## Custom fields

[`FilterField`][pydantic_filters.FilterField] lets the public field name differ
from the target column and accepts the same validation and schema arguments as
Pydantic's `Field`:

```python
from pydantic_filters import BaseFilter, FilterField, FilterType


class CarFilter(BaseFilter):
    include_color: list[str] = FilterField(target="color")
    exclude_color: list[str] = FilterField(
        target="color",
        type_=FilterType.ne,
        description="Colors to exclude",
    )
    minimum_year: int = FilterField(target="year", type_="ge", ge=1886)
```

You may use Pydantic's `Field` directly when only validation or schema metadata
is needed:

```python
from pydantic import Field


class UserFilter(BaseFilter):
    age__lt: int = Field(gt=0, le=150)
```

## Configuration

Set filter-specific options in `model_config`, alongside normal Pydantic
configuration keys. [`FilterConfigDict`][pydantic_filters.FilterConfigDict]
documents their types.

| Option | Default | Purpose |
| --- | --- | --- |
| `delimiter` | `"__"` | Separates a target name from its suffix. Must contain at least two underscores. |
| `optional` | `True` | Makes otherwise-required fields default to `None`. |
| `default_filter_type` | `FilterType.eq` | Used when no known suffix or explicit type is present. |
| `default_search_type` | `SearchType.case_insensitive` | Used when `SearchField` has no explicit type. |
| `suffixes_map` | `get_suffixes_map()` | Maps recognized suffixes to filter operations. |
| `sequence_types` | `(list, set)` | Annotation origins treated as multi-value fields. |

When overriding the configuration, preserve inherited Pydantic and filter
settings:

```python
from pydantic_filters import BaseFilter, FilterType


class CustomFilter(BaseFilter):
    model_config = {
        **BaseFilter.model_config,
        "delimiter": "___",
        "suffixes_map": {"before": FilterType.lt},
        "sequence_types": (list, set, tuple),
    }

    created_at___before: int
```

# SQLAlchemy

The bundled SQLAlchemy driver translates filter metadata into SQLAlchemy
`Select` expressions. Install SQLAlchemy separately:

```shell
pip install "pydantic-filters" "sqlalchemy>=2"
```

The examples below use SQLAlchemy 2 declarative models:

```python
import sqlalchemy as sa
import sqlalchemy.orm as so


class Base(so.DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str]


class User(Base):
    __tablename__ = "users"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    login: so.Mapped[str]
    full_name: so.Mapped[str]
    age: so.Mapped[int]
    department_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("departments.id"),
    )
    department: so.Mapped[Department] = so.relationship()
```

## Filtering

Define filter fields whose targets match model attributes. A nested filter field
must match a relationship name:

```python
from pydantic_filters import BaseFilter, SearchField


class DepartmentFilter(BaseFilter):
    name: list[str]


class UserFilter(BaseFilter):
    login: list[str]
    age__ge: int
    q: str = SearchField(target=["login", "full_name"])
    department: DepartmentFilter
```

Apply the filter with
[`append_filter_to_statement`][pydantic_filters.drivers.sqlalchemy.append_filter_to_statement]:

```python
from pydantic_filters.drivers.sqlalchemy import append_filter_to_statement


statement = append_filter_to_statement(
    statement=sa.select(User),
    model=User,
    filter_=UserFilter(login=["alice", "bob"], q="eva"),
)
```

It adds conditions equivalent to:

```sql
WHERE users.login IN ('alice', 'bob')
  AND (users.login ILIKE '%eva%' OR users.full_name ILIKE '%eva%')
```

Only explicitly supplied fields are applied. Empty equality sequences match no
rows, empty inequality sequences match every row, and empty search sequences
match no rows.

### Related models

Supplying a nested filter adds a join with the nested conditions in its
`ON` clause:

```python
statement = append_filter_to_statement(
    statement=sa.select(User),
    model=User,
    filter_=UserFilter(
        login=["alice", "bob"],
        department=DepartmentFilter(name=["Engineering"]),
    ),
)
```

The joined relationship is used for filtering but is not automatically loaded
into the returned objects. Add the appropriate SQLAlchemy loader option when
the application also needs the related object:

```python
statement = statement.options(so.joinedload(User.department))
```

Nested joins support multiple levels, self-referential relationships,
many-to-many relationships through `secondary`, and composite foreign keys.

## Counting

[`get_count_statement`][pydantic_filters.drivers.sqlalchemy.get_count_statement]
counts distinct primary-key values after applying a filter:

```python
from pydantic_filters.drivers.sqlalchemy import get_count_statement


count_statement = get_count_statement(
    model=User,
    filter_=UserFilter(department=DepartmentFilter(name=["Engineering"])),
)
```

Composite primary keys are not supported by this helper and raise
[`SupportSaDriverError`][pydantic_filters.drivers.sqlalchemy.SupportSaDriverError].

## Pagination

Use
[`append_pagination_to_statement`][pydantic_filters.drivers.sqlalchemy.append_pagination_to_statement]
with any `BasePagination` implementation:

```python
from pydantic_filters import OffsetPagination
from pydantic_filters.drivers.sqlalchemy import append_pagination_to_statement


statement = append_pagination_to_statement(
    statement=sa.select(User),
    pagination=OffsetPagination(limit=25, offset=50),
)
```

This adds `LIMIT 25 OFFSET 50`.

## Sorting

Use [`append_sort_to_statement`][pydantic_filters.drivers.sqlalchemy.append_sort_to_statement]
with a sort model:

```python
from pydantic_filters import BaseSort, SortByOrder
from pydantic_filters.drivers.sqlalchemy import append_sort_to_statement


statement = append_sort_to_statement(
    statement=sa.select(User),
    model=User,
    sort=BaseSort(sort_by="login", sort_by_order=SortByOrder.desc),
)
```

This adds `ORDER BY users.login DESC`. When `sort_by` is `None`, the statement
is returned unchanged.

## Combine all operations

[`append_to_statement`][pydantic_filters.drivers.sqlalchemy.append_to_statement]
applies filtering, then sorting, then pagination. Every operation is optional:

```python
from pydantic_filters.drivers.sqlalchemy import append_to_statement


statement = append_to_statement(
    statement=sa.select(User),
    model=User,
    filter_=UserFilter(q="eva"),
    sort=BaseSort(sort_by="login"),
    pagination=OffsetPagination(limit=10),
)
```

## Driver errors

The driver raises focused exceptions for invalid metadata or unsupported cases:

- [`AttributeNotFoundSaDriverError`][pydantic_filters.drivers.sqlalchemy.AttributeNotFoundSaDriverError]
  when a filter, search, or sort target does not exist;
- [`RelationshipNotFoundSaDriverError`][pydantic_filters.drivers.sqlalchemy.RelationshipNotFoundSaDriverError]
  when a nested filter has no matching relationship;
- [`SupportSaDriverError`][pydantic_filters.drivers.sqlalchemy.SupportSaDriverError]
  for unsupported operations such as counting a composite primary key.

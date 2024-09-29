
`SQLAlchemy` acts as a driver for working with the database. As in any ORM, let's define the models:

```python
import sqlalchemy as sa
import sqlalchemy.orm as so

class Base(so.DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    chef_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("users.id"))


class User(Base):
    __tablename__ = "users"
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    login: so.Mapped[str]
    full_name: so.Mapped[str]
    age: so.Mapped[int]
    email: so.Mapped[str]
    department_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("departments.id"))

    department: so.Mapped[Department] = so.relationship()
```

## Filter

Define filters and use [`append_filter_to_statement`][pydantic_filters.drivers.sqlalchemy.append_filter_to_statement]:

```python
from typing import List

from pydantic_filters import BaseFilter, SearchField


class DepartmentFilter(BaseFilter):
    chef_id: List[int]


class UserFilter(BaseFilter):
    login: List[str]
    age__lt: int
    department_id: List[int]
    q: str = SearchField(target=["login", "full_name"])
    department: DepartmentFilter
```

### Simple filtration

```python
from pydantic_filters.drivers.sqlalchemy import append_filter_to_statement

stmt = append_filter_to_statement(
    statement=sa.select(User),
    model=User,
    filter_=UserFilter(login=["alice", "bob"], q="Eva"),
)
print(stmt)
```

```sql
SELECT users.id, users.login, users.full_name, users.age, users.department_id
FROM users 
WHERE users.login IN ('alice', 'bob') 
  AND (users.login ILIKE '%Eva%' OR users.full_name ILIKE '%Eva%')
```

### Joined filtration

Almost the same thing:

```python
stmt = append_filter_to_statement(
    statement=sa.select(User),
    model=User,
    filter_=UserFilter(login=["alice", "bob"], department=DepartmentFilter(chef_id=[5])),
)
print(stmt)
```

```sql
SELECT users.id, users.login, users.full_name, users.age, users.department_id 
FROM users 
    JOIN departments AS departments_1 
        ON users.department_id = departments_1.id AND departments_1.chef_id IN (5) 
WHERE users.login IN ('alice', 'bob')
```

!!! note

    It should be noted that joined tables will not be included in the final result.
    You can use `sqlalchemy.orm.joinedload()` to get a second join:
    
    ```python
    stmt = append_filter_to_statement(
        statement=sa.select(User),
        model=User,
        filter_=UserFilter(login=["alice", "bob"], department=DepartmentFilter(chef_id=[5])),
    )
    stmt = stmt.options(so.joinedload(User.department))
    print(stmt)
    ```

    ```sql
    SELECT users.id, users.login, users.full_name, users.age, users.department_id, departments_1.id AS id_1, departments_1.chef_id 
    FROM users 
        JOIN departments AS departments_2 
            ON users.department_id = departments_2.id AND departments_2.chef_id IN (5) 
        LEFT OUTER JOIN departments AS departments_1 ON departments_1.id = users.department_id 
    WHERE users.login IN ('alice', 'bob')
    ```

### Get count

You can also get a statement to get the number of rows satisfying the filter by using the function
[`get_count_statement()`][pydantic_filters.drivers.sqlalchemy.get_count_statement]:

```python
from pydantic_filters.drivers.sqlalchemy import get_count_statement

count_stmt = get_count_statement(
    model=User,
    filter_=UserFilter(login=["alice", "bob"], department=DepartmentFilter(chef_id=[5])),
)
print(count_stmt)
```

```sql
SELECT count(DISTINCT users.id) AS count_1 
FROM users 
    JOIN departments AS departments_1 
        ON users.department_id = departments_1.id AND departments_1.chef_id IN (5) 
WHERE users.login IN ('alice', 'bob')
```

## Pagination

There is a similar function for pagination 
[`append_pagination_to_statement()`][pydantic_filters.drivers.sqlalchemy.append_pagination_to_statement]:

```python
from pydantic_filters import OffsetPagination
from pydantic_filters.drivers.sqlalchemy import append_pagination_to_statement

stmt = append_pagination_to_statement(
    statement=sa.select(User),
    pagination=OffsetPagination(limit=1000, offset=4000),
)
print(stmt)
```

```sql
SELECT users.id, users.login, users.full_name, users.age, users.department_id 
FROM users 
LIMIT 1000 OFFSET 4000
```

## Sort

And for Sort [`append_sort_to_statement()`][pydantic_filters.drivers.sqlalchemy.append_sort_to_statement]:

```python
from pydantic_filters import BaseSort, SortByOrder
from pydantic_filters.drivers.sqlalchemy import append_sort_to_statement

stmt = append_sort_to_statement(
    statement=sa.select(User),
    model=User,
    sort=BaseSort(sort_by="login", sort_by_order=SortByOrder.desc),
)
print(stmt)
```

```sql
SELECT users.id, users.login, users.full_name, users.age, users.department_id 
FROM users 
ORDER BY users.login DESC
```

## All in one

[`append_to_statement()`][pydantic_filters.drivers.sqlalchemy.append_to_statement] - all-in-one function:

```python
from pydantic_filters.drivers.sqlalchemy import append_to_statement

stmt = append_to_statement(
    statement=sa.select(User),
    model=User,
    filter_=UserFilter(q="Eva"),
    pagination=OffsetPagination(limit=10),
    sort=BaseSort(sort_by="login"),
)
print(stmt)
```

```sql
SELECT users.id, users.login, users.full_name, users.age, users.department_id 
FROM users 
WHERE users.login ILIKE '%%Eva%%' OR users.full_name ILIKE '%%Eva%%' 
ORDER BY users.login ASC 
LIMIT 10 OFFSET 0
```

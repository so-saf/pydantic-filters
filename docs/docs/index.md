---
hide:
  - navigation
  - toc
---

# pydantic-filters

[![Testing](https://github.com/so-saf/pydantic-filters/actions/workflows/test.yaml/badge.svg)](https://github.com/so-saf/pydantic-filters/actions/workflows/test.yaml)
[![pypi](https://img.shields.io/pypi/v/pydantic-filters.svg)](https://pypi.org/project/pydantic-filters/)
[![license](https://img.shields.io/github/license/so-saf/pydantic-filters.svg)](https://github.com/so-saf/pydantic-filters/blob/master/LICENSE)
[![versions](https://img.shields.io/pypi/pyversions/pydantic-filters.svg)](https://pypi.org/project/pydantic-filters/)

Define filters as Pydantic models, then translate them into queries with a driver.
`pydantic-filters` also provides reusable pagination and sorting models and a
FastAPI integration.

## Requirements

- Python 3.10 or newer (including Python 3.14 and 3.15)
- Pydantic 2
- SQLAlchemy 2 or newer when using the SQLAlchemy driver
- FastAPI 0.100 or newer when using the FastAPI plugin

Only Pydantic is installed as a required dependency. Install an integration
alongside the package when you need it:

```shell
pip install pydantic-filters
pip install "pydantic-filters" "sqlalchemy>=2"
pip install "pydantic-filters" "fastapi>=0.100"
```

## Quick start

Define an SQLAlchemy model and a matching filter:

```python
import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic_filters import BaseFilter
from pydantic_filters.drivers.sqlalchemy import append_filter_to_statement


class Base(so.DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str]
    age: so.Mapped[int]


class UserFilter(BaseFilter):
    id: list[int]
    name__ilike: str
    age__ge: int


filter_ = UserFilter(name__ilike="kate", age__ge=18)
statement = append_filter_to_statement(
    statement=sa.select(User),
    model=User,
    filter_=filter_,
)
```

The resulting statement contains conditions equivalent to:

```sql
WHERE users.name ILIKE 'kate' AND users.age >= 18
```

Fields that were not supplied are ignored. Although filter models inherit from
Pydantic's `BaseModel`, their fields are not required by default.

## Where to go next

- [Filters](usage/filters.md): operators, search fields, nested filters, and configuration
- [SQLAlchemy](usage/sqlalchemy.md): apply filtering, sorting, and pagination to statements
- [FastAPI](usage/fastapi.md): expose flat query parameters, including nested filters
- [Pagination](usage/pagination.md) and [sorting](usage/sort.md): built-in and custom models

**Source code:** [github.com/so-saf/pydantic-filters](https://github.com/so-saf/pydantic-filters)

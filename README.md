# pydantic-filters

[![Testing](https://github.com/so-saf/pydantic-filters/actions/workflows/test.yaml/badge.svg)](https://github.com/so-saf/pydantic-filters/actions/workflows/test.yaml)
[![Coverage](https://codecov.io/gh/so-saf/pydantic-filters/branch/master/graph/badge.svg)](https://codecov.io/gh/so-saf/pydantic-filters)
[![PyPI](https://img.shields.io/pypi/v/pydantic-filters.svg)](https://pypi.org/project/pydantic-filters/)
[![Python](https://img.shields.io/pypi/pyversions/pydantic-filters.svg)](https://pypi.org/project/pydantic-filters/)
[![License](https://img.shields.io/github/license/so-saf/pydantic-filters.svg)](LICENSE)

Define filters as Pydantic models, then translate them into queries with a
driver. The package also provides reusable pagination and sorting models and a
FastAPI integration.

**Documentation:** https://so-saf.github.io/pydantic-filters/

## Requirements

- Python 3.10 or newer, including Python 3.14 and 3.15
- Pydantic 2
- SQLAlchemy 2 or newer when using the SQLAlchemy driver
- FastAPI 0.100 or newer when using the FastAPI plugin

Only Pydantic is a required dependency. Install integrations separately:

```shell
pip install pydantic-filters
pip install "pydantic-filters" "sqlalchemy>=2"
pip install "pydantic-filters" "fastapi>=0.100"
```

## Quick start

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

The statement contains conditions equivalent to:

```sql
WHERE users.name ILIKE 'kate' AND users.age >= 18
```

Filter fields are not required by default, and fields that were not supplied
are ignored by the driver. See the documentation for:

- [operators, search fields, nested filters, and configuration](https://so-saf.github.io/pydantic-filters/usage/filters/);
- [SQLAlchemy filtering, counting, sorting, and pagination](https://so-saf.github.io/pydantic-filters/usage/sqlalchemy/);
- [FastAPI query-parameter integration](https://so-saf.github.io/pydantic-filters/usage/fastapi/).

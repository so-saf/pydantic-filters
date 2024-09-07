
# pydantic-filters

[![Testing](https://github.com/so-saf/pydantic-filters/actions/workflows/test.yaml/badge.svg)](https://github.com/so-saf/pydantic-filters/actions/workflows/test.yaml)
[![Coverage](https://codecov.io/gh/so-saf/pydantic-filters/branch/main/graph/badge.svg)](https://codecov.io/gh/so-saf/pydantic-filters)
[![pypi](https://img.shields.io/pypi/v/pydantic-filters.svg)](https://pypi.python.org/pypi/pydantic-filters)
[![license](https://img.shields.io/github/license/so-saf/pydantic-filters.svg)](https://github.com/so-saf/pydantic-filters/blob/main/LICENSE)
[![versions](https://img.shields.io/pypi/pyversions/pydantic-filters.svg)](https://github.com/so-saf/pydantic-filters)

**Source Code:** https://github.com/so-saf/pydantic-filters

---

Describe the filters, not implement them! 
A declarative and intuitive way to describe data filtering and sorting in your application.

The only required dependency is Pydantic.
You can use the basic features without being attached to specific frameworks, 
or use one of the supported plugins and drivers:
 
Plugins:
* FastAPI >= 0.100.0

Drivers: 
* SQLAlchemy >= 2

## Installation

```shell
pip install pydantic-filters
```

# A Simple Example

`BaseFilter` is just a pydantic model, it should be treated similarly

Let's imagine you have a simple user service with the following SQLAlchemy model:


```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    age: Mapped[int]
```

Describe how you would like to filter users using BaseFilter.

```python
from typing import List
from pydantic_filters import BaseFilter


class UserFilter(BaseFilter):
    id: List[int]
    name: List[str]
    name__ilike: str
    age__lt: int
    age__gt: int
```

`BaseFilter` is just a pydantic model, it should be treated similarly

Next, you need to apply a filter to some query:

```python
from sqlalchemy import select
from pydantic_filters.drivers.sqlalchemy import append_filter_to_statement

statement = select(User)
filter_ = UserFilter(name__ilike="kate", age__lt=23)

stmt = append_filter_to_statement(
    statement=statement, model=User, filter_=filter_,
)
```

And get something like:

```sql
SELECT users.id, users.name, users.age 
FROM users 
WHERE users.name ILIKE 'kate' AND users.age < 23
```

The filter can be used in conjunction with one of the supported web frameworks:

```python
from typing import Annotated
from fastapi import FastAPI, APIRouter
from pydantic_filters.plugins.fastapi import FilterDepends


router = APIRouter()


@router.get("/")
async def get_multiple(
    filter_: Annotated[UserFilter, FilterDepends(UserFilter)],
):
    ...


app = FastAPI(title="User Service")
app.include_router(router, prefix="/users", tags=["User"])
```

![fastapi-simple-example.png](docs/statics/fastapi-simple-example.png)

# API Reference

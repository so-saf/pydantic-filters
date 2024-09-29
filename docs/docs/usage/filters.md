
# Filter

## Introduction

Any web application manipulates data and pydantic models help a lot in this. 
They accompany our application from validating the data in the API to serializing it in a query in the database.
So pydantic models are some abstract schemas running back and forth. At least that's how I see it :) 
The same way can apply in filtering: define a schema and use it.

## Basic BaseFilter usage

[`BaseFilter`][pydantic_filters.BaseFilter] is a pydantic model.

Let's define a user schema and filters to it:

```python
from typing import List

from pydantic import BaseModel
from pydantic_filters import BaseFilter, SearchField

class UserSchema(BaseModel):
    id: int
    login: str
    full_name: str
    age: int
    email: str
    department_id: int


class UserFilter(BaseFilter):
    login: List[str]
    login__n: List[str]
    age__lt: int
    age__gt: int
    department_id: List[int]
    department_id__n: List[int]
    q: str = SearchField(target=["login", "name", "email"]) 
```

??? info

    Unlike `BaseModel`, all fields in `BaseFilter` are optional. 
    This is probably the only major difference between filter models and pydantic models.
    This behavior can be changed in the configuration,
    see [`FilterConfigDict.optional`][pydantic_filters.FilterConfigDict.optional].

    A `UserFilter` is equivalent to the following pydantic model:

    ```python
    class UserFilterEquivalent(BaseModel):
        login: List[str] = None
        login__n: List[str] = None
        age__lt: int = None
        age__gt: int = None
        department_id: List[int] = None
        department_id__n: List[int] = None
        q: str = None 
    ```

    Any field can be made required, you just need to add `Ellipsis`: 
    
    ```python
    id: int = ...
    ```

There are seven filters defined in `UserFilter`:

- `login` - list of include strings.
- `login__n` - list of excluding strings.
- `age__lt` - maximum age.
- `age__gt` - minimum age.
- `department_id` - list of including numbers.
- `department_id__n` - list of excluding numbers.
- `q` - search field by login, name or e-mail.

The `UserFilter(department_id=[3, 4], age__gt=18)` condition will be interpreted as:

> All users over 18 years of age from department number 3 OR 4.

As you may have already noticed, how a field will be filtered is determined 
by the field suffix and the type annotation:

- `login: str` ~ `login = value`
- `login: List[str]` ~ `login IN (value1, value2, ...)`
- `login__n: List[str]` ~ `login NOT IN (value1, value2, ...)`
- `age__gt: int` ~ `age >= value`
- `age__gt: List[int]` ~ `age >= value1 OR age >= value2 OR ...`

!!! note

    The complete list of operators is defined in [`FilterType`][pydantic_filters.FilterType].

!!! tip

    You can override the available suffixes and their associated operators in the model configuration
    [`FilterConfigDict.suffixes_map`][pydantic_filters.FilterConfigDict.suffixes_map].

## Related fields filtering

Quite often there is a need to filter on related tables in the database. 
In addition to the user schema, let's define the department schema:

```python
from typing import List

from pydantic import BaseModel
from pydantic_filters import BaseFilter, SearchField

class DepartmentSchema(BaseModel):
    id: int
    chef_id: int


class UserSchema(BaseModel):
    id: int
    login: str
    full_name: str
    age: int
    email: str
    department_id: int
    
    
class DepartmentFilter(BaseFilter):
    chef_id: List[int]
    chef_id__n: List[int]


class UserFilter(BaseFilter):
    login: List[str]
    login__n: List[str]
    age__lt: int
    age__gt: int
    department_id: List[int]
    department_id__n: List[int]
    q: str = SearchField(target=["login", "full_name", "email"])
    # Related filter!
    department: DepartmentFilter
```

??? warning

    Support for filtering by related models depends on the driver you are using.
    
    For example, in the case of SQLAlchemy:

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
    
        department: so.Mapped[Department] = so.relationship(foreign_keys="User.department_id")
    ```

    Here, `department_id` is defined as a foreign key 
    and `department` provides access to the external table.

## Fields

The [`FilterField`][pydantic_filters.FilterField] and [`SearchField`][pydantic_filters.SearchField] 
functions are used to customize and add metadata to model fields.

### Target and Type setting

When defining a filter for each field, the target attribute name (`target`) and the filter type (`type`) are defined.

The following two filters are equivalents:

```python
from typing import List

from pydantic_filters import BaseFilter, FilterField

class CarFilter(BaseFilter):
    color: List[str]
    color__n: List[str]


class DirectCarFilter(BaseFilter):
    color: List[str] = FilterField(target="color", type_="eq")
    color__n: List[str] = FilterField(target="color", type_="ne")
```

But sometimes it may be necessary to name fields differently:

```python
from typing import List

from pydantic_filters import BaseFilter, FilterField

class DirectCarFilter(BaseFilter):
    include_color: List[str] = FilterField(target="color", type_="eq")
    exclude_color: List[str] = FilterField(target="color", type_="ne")
```

### Pydantic compatibility

Both functions [`FilterField`][pydantic_filters.FilterField] and [`SearchField`][pydantic_filters.SearchField]
are compatible with the `pydantic.Field` and will work as if the arguments were passed directly to it.

```python
from pydantic import Field
from pydantic_filters import BaseFilter, FilterField

class UserFilter(BaseFilter):
    age__lt: int = FilterField(gt=0, le=100)
    age__gt: int = Field(gt=0, le=100)  # The same
```

??? Tip
    
    The next option is also possible:

    ```python
    from typing import List
    
    from pydantic import Field
    from pydantic_filters import BaseFilter, FilterField
    
    class CarFilter(BaseFilter):
        exclude_color: List[str] = Field(
            default=FilterField(target="color", type_="ne"), 
            pattern="^#(?:[0-9a-fA-F]{3}){1,2}$",
        )
    ```

## Configuration

As in pydantic, filter behavior can be controlled using [`FilterConfigDict`][pydantic_filters.FilterConfigDict].

### delimiter

Specifies the delimiter for the suffix. Defaults to `__`.

### optional

By default, all fields are optional.
When `optional = False` the filter behavior does not differ from `pydantic.BaseModel`.

### default_filter_type

Filter type in case it cannot be “guessed”. The default is [`FilterType.eq`][pydantic_filters.FilterType.eq].

### default_search_type

Search type in case it cannot be “guessed”. 
The default is [`SearchType.case_insensitive`][pydantic_filters.SearchType.case_insensitive].

### suffixes_map

Map the prefix mapping to the filter type. 
Defined by the function [`get_suffixes_map`][pydantic_filters.get_suffixes_map].

### sequence_types

List of types whose annotations are taken as sequences. The default is `(list, set)`.

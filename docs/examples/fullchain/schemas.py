from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from pydantic_filters import BaseFilter, BasePagination, BaseSort, SearchField


class AddressCreateSchema(BaseModel):
    city: str
    postal_code: int


class AddressGetSchema(BaseModel):
    id: int
    city: str
    postal_code: int


class AddressUpdateSchema(BaseModel):
    city: Optional[str] = None
    postal_code: Optional[int] = None


class AddressFilter(BaseFilter):
    q: str = SearchField(target=["city"])
    city: List[str]
    postal_code: List[int]


class AddressSortByEnum(str, Enum):
    id = "id"
    name = "city"
    postal_code = "postal_code"


class AddressSort(BaseSort):
    sort_by: AddressSortByEnum


class UserCreateSchema(BaseModel):
    name: str
    age: int
    address_id: int


class UserGetSchema(BaseModel):
    id: int
    name: str
    address_id: int

    address: AddressGetSchema


class UserUpdateSchema(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    address_id: Optional[int] = None


class UserFilter(BaseFilter):
    q: str = SearchField(target=["name"])
    name: List[str]
    address_id: List[int]
    address_id__n: List[int]
    age__lt: int
    age__le: int
    age__gt: int
    age__ge: int

    address: AddressFilter


class UserSortByEnum(str, Enum):
    id = "id"
    name = "name"
    age = "age"


class UserSort(BaseSort):
    sort_by: UserSortByEnum


class Pagination(BasePagination):
    limit: int = Field(100, le=1000, gt=0)
    offset: int = Field(0, ge=0)

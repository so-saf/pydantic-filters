from typing import Generic, List, TypeVar

from fastapi import APIRouter, Path
from pydantic import BaseModel
from typing_extensions import Annotated

from pydantic_filters.plugins.fastapi import FilterDepends, PaginationDepends, SortDepends

from . import schemas
from .services import address_service, user_service

_T = TypeVar("_T")


class MultipleResponse(BaseModel, Generic[_T]):
    limit: int
    offset: int
    data: List[_T]


address_router = APIRouter()


@address_router.post("/")
def create_address(data: schemas.AddressCreateSchema) -> schemas.AddressGetSchema:
    return address_service.create(data)


@address_router.get("/")
def get_multiple_addresses(
        pagination: schemas.Pagination = PaginationDepends(schemas.Pagination),
        sort: schemas.AddressSort = SortDepends(schemas.AddressSort),
        filter_: schemas.AddressFilter = FilterDepends(schemas.AddressFilter),
) -> MultipleResponse[schemas.AddressGetSchema]:
    return MultipleResponse.model_construct(
        limit=pagination.limit,
        offset=pagination.offset,
        data=address_service.get_multiple(pagination, sort, filter_),
    )


@address_router.get("/{id}")
def get_address(id_: Annotated[int, Path(alias="id")]) -> schemas.AddressGetSchema:
    return address_service.get(id_)


@address_router.patch("/{id}")
def update_address(
        id_: Annotated[int, Path(alias="id")],
        data: schemas.AddressUpdateSchema,
) -> schemas.AddressGetSchema:
    return address_service.update(id_, data)


@address_router.delete("/{id}", status_code=204)
def delete_address(id_: Annotated[int, Path(alias="id")]) -> None:
    return address_service.delete(id_)


user_router = APIRouter()


@user_router.post("/")
def create_user(data: schemas.UserCreateSchema) -> schemas.UserGetSchema:
    return user_service.create(data)


@user_router.get("/")
def get_multiple_users(
        pagination: schemas.Pagination = PaginationDepends(schemas.Pagination),
        sort: schemas.UserSort = SortDepends(schemas.UserSort),
        filter_: schemas.UserFilter = FilterDepends(schemas.UserFilter),
) -> MultipleResponse[schemas.UserGetSchema]:
    return MultipleResponse.model_construct(
        limit=pagination.limit,
        offset=pagination.offset,
        data=user_service.get_multiple(pagination, sort, filter_),
    )


@user_router.get("/{id}")
def get_user(id_: Annotated[int, Path(alias="id")]) -> schemas.UserGetSchema:
    return user_service.get(id_)


@user_router.patch("/{id}")
def update_user(
        id_: Annotated[int, Path(alias="id")],
        data: schemas.UserUpdateSchema,
) -> schemas.UserGetSchema:
    return user_service.update(id_, data)


@user_router.delete("/{id}", status_code=204)
def delete_user(id_: Annotated[int, Path(alias="id")]) -> None:
    return user_service.delete(id_)

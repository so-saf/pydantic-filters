from typing import List

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from pydantic_filters.drivers.sqlalchemy import (
    append_filter_to_statement,
    append_pagination_to_statement,
    append_sort_to_statement,
)

from . import schemas
from .database import AddressModel, Base, UserModel


class AddressService:

    def __init__(self, sessionmaker_: sessionmaker[Session]) -> None:
        self.sessionmaker = sessionmaker_

    def create(self, data: schemas.AddressCreateSchema) -> schemas.AddressGetSchema:
        with self.sessionmaker() as session:
            address = AddressModel(**data.model_dump(exclude_unset=True))
            session.add(address)
            session.commit()
            return schemas.AddressGetSchema.model_validate(address, from_attributes=True)

    def get(self, id_: int) -> schemas.AddressGetSchema:
        with self.sessionmaker() as session:
            address = session.get(id_, AddressModel)
            return schemas.AddressGetSchema.model_validate(address, from_attributes=True)

    def get_multiple(
            self,
            pagination: schemas.Pagination,
            sort: schemas.AddressSort,
            filter_: schemas.AddressFilter,
    ) -> List[schemas.AddressGetSchema]:
        with self.sessionmaker() as session:
            statement = select(AddressModel)
            statement = append_pagination_to_statement(statement, pagination)
            statement = append_sort_to_statement(statement, sort, AddressModel)
            statement = append_filter_to_statement(statement, filter_, AddressModel)
            return [
                schemas.AddressGetSchema.model_validate(a, from_attributes=True)
                for a in session.scalars(statement)
            ]

    def update(self, id_: int, data: schemas.AddressUpdateSchema) -> schemas.AddressGetSchema:
        with self.sessionmaker() as session:
            address = session.get(id_, AddressModel)
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(address, key, value)
            session.commit()
            return schemas.AddressGetSchema.model_validate(address, from_attributes=True)

    def delete(self, id_: int) -> None:
        with self.sessionmaker() as session:
            address = session.get(AddressModel, id_)
            if not address:
                return
            session.delete(address)
            session.commit()


class UserService:

    def __init__(self, sessionmaker_: sessionmaker[Session]) -> None:
        self.sessionmaker = sessionmaker_

    def create(self, data: schemas.UserCreateSchema) -> schemas.UserGetSchema:
        with self.sessionmaker() as session:
            user = UserModel(**data.model_dump(exclude_unset=True))
            session.add(user)
            session.commit()
            return schemas.UserGetSchema.model_validate(user, from_attributes=True)

    def get(self, id_: int) -> schemas.UserGetSchema:
        with self.sessionmaker() as session:
            user = session.get(id_, UserModel)
            return schemas.UserGetSchema.model_validate(user, from_attributes=True)

    def get_multiple(
            self,
            pagination: schemas.Pagination,
            sort: schemas.UserSort,
            filter_: schemas.UserFilter,
    ) -> List[schemas.UserGetSchema]:
        with self.sessionmaker() as session:
            statement = select(UserModel)
            statement = append_pagination_to_statement(statement, pagination)
            statement = append_sort_to_statement(statement, sort, UserModel)
            statement = append_filter_to_statement(statement, filter_, UserModel)
            return [
                schemas.UserGetSchema.model_validate(a, from_attributes=True)
                for a in session.scalars(statement)
            ]

    def update(self, id_: int, data: schemas.UserUpdateSchema) -> schemas.UserGetSchema:
        with self.sessionmaker() as session:
            user = session.get(id_, UserModel)
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(user, key, value)
            session.commit()
            return schemas.UserGetSchema.model_validate(user, from_attributes=True)

    def delete(self, id_: int) -> None:
        with self.sessionmaker() as session:
            user = session.get(UserModel, id_)
            if not user:
                return
            session.delete(user)
            session.commit()


engine = create_engine("sqlite:///database.db", echo=False)
sm = sessionmaker(engine, autoflush=False)
Base.metadata.create_all(engine)

address_service = AddressService(sm)
user_service = UserService(sm)

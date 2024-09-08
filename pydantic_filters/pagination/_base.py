from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class PaginationInterface(BaseModel, ABC):

    @abstractmethod
    def get_limit(self) -> int:
        ...

    @abstractmethod
    def get_offset(self) -> int:
        ...


class OffsetPagination(PaginationInterface):
    limit: int = Field(100, ge=1)
    offset: int = Field(0, ge=0)

    def get_limit(self) -> int:
        return self.limit

    def get_offset(self) -> int:
        return self.offset


class PagePagination(PaginationInterface):
    page: int = Field(1, ge=1)
    per_page: int = Field(100, ge=1)

    def get_limit(self) -> int:
        return self.per_page

    def get_offset(self) -> int:
        return (self.page - 1) * self.per_page

from abc import abstractmethod

from pydantic import BaseModel, Field


class BasePagination(BaseModel):
    """
    The pagination implementation must be a Pydantic model
    and implement two methods: get_limit and get_offset.
    """

    @abstractmethod
    def get_limit(self) -> int:
        """Limit Getter."""

    @abstractmethod
    def get_offset(self) -> int:
        """Offset Getter."""


class OffsetPagination(BasePagination):
    """
    Limit-Offset Pagination implementation.
    """

    limit: int = Field(100, ge=1)
    """Limit field"""

    offset: int = Field(0, ge=0)
    """Offset field"""

    def get_limit(self) -> int:
        return self.limit

    def get_offset(self) -> int:
        return self.offset


class PagePagination(BasePagination):
    """
    Page-PerPage Pagination implementation.
    """

    page: int = Field(1, ge=1)
    """Page number field"""

    per_page: int = Field(100, ge=1)
    """Items per page field"""

    def get_limit(self) -> int:
        return self.per_page

    def get_offset(self) -> int:
        return (self.page - 1) * self.per_page

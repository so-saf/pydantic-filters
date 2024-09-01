from enum import Enum

__all__ = (
    "SortByOrder",
)


class SortByOrder(str, Enum):
    asc = "asc"
    desc = "desc"

from enum import Enum


class SortByOrder(str, Enum):
    asc = "asc"
    """ascending"""

    desc = "desc"
    """descending"""

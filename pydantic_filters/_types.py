import sys
from typing import List, Type, TypeVar

__all__ = (
    "NoneType",
    "GenericAlias",
    "Annotation",
)

from typing_extensions import TypeAlias, Union

if sys.version_info >= (3, 10):
    from types import NoneType
else:
    NoneType = type(None)

if sys.version_info >= (3, 9):
    from types import GenericAlias
else:
    GenericAlias = type(List[int])


Annotation: TypeAlias = Union[GenericAlias, None, Type, TypeVar]

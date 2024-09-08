import sys
from typing import List, Type, TypeVar

__all__ = (
    "NoneType",
    "GenericAlias",
    "Annotation",
)

from typing_extensions import TypeAlias, Union

if sys.version_info >= (3, 10):  # pragma: no cover
    from types import NoneType
else:  # pragma: no cover
    NoneType = type(None)

if sys.version_info >= (3, 9):  # pragma: no cover
    from types import GenericAlias
else:  # pragma: no cover
    GenericAlias = type(List[int])


Annotation: TypeAlias = Union[GenericAlias, None, Type, TypeVar]

from typing import Collection

from pydantic.fields import FieldInfo


def __field_info_eq__(__f1: FieldInfo, __f2: FieldInfo, /, *, exclude: Collection[str] = tuple()) -> bool:
    if not all(
            isinstance(f, FieldInfo)
            for f in (__f1, __f2)
    ):
        return False

    return all(
        getattr(__f1, attr) == getattr(__f2, attr)
        for attr in FieldInfo.__slots__
        if not attr.startswith("_") and attr not in exclude
    )

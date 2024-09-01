from typing import Collection

import pytest
from pydantic.fields import FieldInfo, Field

from tests.misc import (
    __field_info_eq__,
)


@pytest.mark.parametrize(
    "f1, f2, exclude, res",
    [
        (Field(), Field(), (), True),
        (Field(None), Field(None), (), True),
        (Field(le=1), Field(le=1), (), True),
        (Field(le=2), Field(le=1), (), False),
        (FieldInfo(annotation=str), FieldInfo(), (), False),
        (FieldInfo(annotation=str), FieldInfo(), ("annotation",), True),
        (Field(), "Field", (), False)
    ],
)
def test_is_field_infos_equal(f1: FieldInfo, f2: FieldInfo, exclude: Collection[str], res: bool):
    assert __field_info_eq__(f1, f2, exclude=exclude) == res

import pytest

from pydantic_filters import FilterField, SearchField, FilterType
from pydantic_filters.filter._fields import _BaseField


class FieldTest(_BaseField):
    
    __slots__ = 'a', 'b'
    
    def __init__(self, a, b):
        self.a = a
        self.b = b
        super().__init__()


class Field2Test(_BaseField):
    __slots__ = 'a', 'b'

    def __init__(self, a, b):
        self.a = a
        self.b = b
        super().__init__()


@pytest.mark.parametrize(
    "f1, f2, res",
    [
        (FieldTest(1, 2), FieldTest(1, 2), True),
        (FieldTest(1, 2), FieldTest(1, -2), False),
        (FieldTest(1, 2), Field2Test(1, 2), False),
    ]
)
def test_eq(f1: FieldTest, f2: FieldTest, res: bool):
    assert (f1 == f2) is res
    
    
@pytest.mark.parametrize(
    "f, res_str, res_repr",
    [
        (FieldTest(1, 2), "a=1 b=2", "FieldTest(a=1, b=2)"),
        (FieldTest(1, None), "a=1", "FieldTest(a=1)"),
        (FieldTest(None, None), "", "FieldTest()"),
    ]
)
def test_repr(f: FieldTest, res_str: str, res_repr: str):
    assert str(f) == res_str
    assert repr(f) == res_repr
    

def test_filter_field():
    assert FilterField(type_="eq") == FilterField(type_=FilterType.eq)
    
    with pytest.raises(ValueError):
        FilterField(type_="")
        
        
def test_search_field():
    with pytest.raises(ValueError):
        SearchField(target=[])
        
    with pytest.raises(ValueError):
        SearchField(target=["a"], type_="")

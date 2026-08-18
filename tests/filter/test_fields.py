import pytest
from pydantic_core import PydanticUndefined

from pydantic_filters import FilterField, SearchField, FilterType, SearchType
from pydantic_filters.filter._fields import BaseField, FilterFieldInfo, SearchFieldInfo


class FieldTest(BaseField):
    
    __slots__ = 'a', 'b'
    
    def __init__(self, a, b):
        self.a = a
        self.b = b
        super().__init__()


class Field2Test(BaseField):
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


def test_filter_field_preserves_default_and_pydantic_kwargs():
    field = FilterField(10, target="user_id", type_="ge", title="Minimum user", ge=1)

    assert field == FilterFieldInfo(
        target="user_id",
        type_=FilterType.ge,
        field_kwargs={"default": 10, "title": "Minimum user", "ge": 1},
    )


def test_filter_field_uses_undefined_default_by_default():
    assert FilterField().field_kwargs == {"default": PydanticUndefined}


def test_search_field_preserves_target_type_and_kwargs():
    field = SearchField(None, target=("name", "email"), type_="case_sensitive", description="Search")

    assert field == SearchFieldInfo(
        target=("name", "email"),
        type_=SearchType.case_sensitive,
        field_kwargs={"default": None, "description": "Search"},
    )


def test_field_kwargs_are_independent_between_instances():
    first = FilterField(title="first")
    second = FilterField(title="second")

    first.field_kwargs["title"] = "changed"
    assert second.field_kwargs["title"] == "second"

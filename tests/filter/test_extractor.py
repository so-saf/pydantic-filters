from functools import partialmethod
from typing import Tuple, Type, List, Set, Union, Optional, Dict
from unittest import mock

import pytest
from pydantic import BaseModel
from pydantic.fields import FieldInfo, Field
from pydantic_core import PydanticUndefined

from pydantic_filters import FilterType, BaseFilter, SearchType, SearchField, FilterField
from pydantic_filters.filter._extractors import (
    NestedFilterExtractor,
    SearchFieldExtractor,
    FilterFieldExtractor,
    is_filter_subclass,
    _is_sequence,
    _simplify_optional_annotation,
    _get_defaults_dict_to_override,
)
from pydantic_filters.filter._fields import FilterFieldInfo, SearchFieldInfo
from tests.misc import __field_info_eq__


@pytest.mark.parametrize(
    "base, res",
    [
        (BaseFilter, True),
        (type("ChildKlass", (BaseFilter,), {}), True),
        (BaseModel, False),
        (type("ChildKlass", (BaseModel,), {}), False),
        (object, False),
    ]
)
def test_is_filter_subclass(base: Type, res: bool):
    assert is_filter_subclass(type("Klass", (base,), {}), ) is res
    
    
def test_is_filter_subclass_for_instance():
    assert is_filter_subclass(...) is False


@pytest.mark.parametrize(
    "ann, res_ann",
    [
        (str, str),
        (Optional[str], str),
        (Optional[List[str]], List[str]),
        (Optional[Union[str, int]], Union[str, int, None]),
        (Union[str, int, None], Union[str, int, None])
    ]
)
def test_simplify_annotation(ann: Type, res_ann: Type):
    assert _simplify_optional_annotation(ann) == res_ann


@pytest.mark.parametrize(
    "ann, res",
    [
        (str, False),
        (List[int], True),
        (Set[int], True),
        (Union[List[str], None], True),
        (Union[List[str], str, None], False),
    ]
)
def test_is_sequence(ann: Type, res: bool) -> None:
    sequence_types = (list, set)
    assert _is_sequence(ann, sequence_types) is res


@pytest.mark.parametrize(
    "field_info, optional, res_dict",
    [
        (Field(), True, {"default": None}),
        (Field(), False, {"default": PydanticUndefined}),
        (Field(...), True, {"default": PydanticUndefined}),
        (Field(...), False, {"default": PydanticUndefined}),
        (Field("asdf"), True, {}),
        (Field("asdf"), False, {})
    ]
)
def test_get_default_dict_to_override(field_info: FieldInfo, optional: bool, res_dict: Dict):
    assert _get_defaults_dict_to_override(field_info, optional=optional) == res_dict
    

class NestedModel(BaseModel):
    pass


class TestNestedFilterExtractor:
    
    class ModelTest(BaseModel):
        n1: NestedModel
        n2: NestedModel = ...
        n3: Optional[NestedModel]
        n4: NestedModel = NestedModel()
        n5: NestedModel = "aboba"
        
        nr1: NestedModel = FilterField()
        nr2: NestedModel = SearchField(target=["a"])

    @mock.patch.object(FieldInfo, "__eq__", new=partialmethod(__field_info_eq__, exclude=["annotation"]))
    @pytest.mark.parametrize(
        "name, optional, res_field_info",
        [
            ("n1", True, Field(None)),
            ("n1", False, Field()),
            ("n2", True, Field()),
            ("n2", False, Field()),
            ("n3", True, Field(None)),
            ("n3", False, Field()),
            ("n4", True, Field(NestedModel())),
            ("n4", False, Field(NestedModel())),
            ("n5", True, Field("aboba")),
            ("n5", False, Field("aboba")),
        ]
    )
    def test_call(self, name: str, optional: bool, res_field_info: FieldInfo):
        extractor = NestedFilterExtractor(optional=optional)
        field_info, nested_model = extractor(name, self.ModelTest.model_fields[name])
        assert nested_model == NestedModel
        assert field_info == res_field_info
        
    @pytest.mark.parametrize("name", ["nr1", "nr2"])
    def test_raise_call(self, name: str):
        with pytest.raises(ValueError):
            extractor = NestedFilterExtractor(optional=True)
            extractor(name, self.ModelTest.model_fields[name])


class TestSearchFieldExtractor:
    
    class ModelTest(BaseModel):
        q1: str = SearchField(target=["a"])
        q2: List[str] = SearchField(target=["a"])
        q3: str = SearchField(..., target=["a"])

    @mock.patch.object(FieldInfo, "__eq__", new=partialmethod(__field_info_eq__, exclude=["annotation"]))
    @pytest.mark.parametrize(
        "name, optional, res_field_info, res_search_field_info",
        [
            ("q1", True, Field(None), 
             SearchFieldInfo(target=["a"], type_=SearchType.case_insensitive, is_sequence=False)),
            ("q1", False, Field(),
             SearchFieldInfo(target=["a"], type_=SearchType.case_insensitive, is_sequence=False)),
            ("q2", True, Field(None),
             SearchFieldInfo(target=["a"], type_=SearchType.case_insensitive, is_sequence=True)),
            ("q2", False, Field(),
             SearchFieldInfo(target=["a"], type_=SearchType.case_insensitive, is_sequence=True)),
            ("q3", True, Field(),
             SearchFieldInfo(target=["a"], type_=SearchType.case_insensitive, is_sequence=False)),
            ("q3", False, Field(),
             SearchFieldInfo(target=["a"], type_=SearchType.case_insensitive, is_sequence=False)),
        ]
    )
    def test_call(
            self, 
            name: str, 
            optional: bool, 
            res_field_info: FieldInfo, 
            res_search_field_info: SearchFieldInfo,
    ):
        extractor = SearchFieldExtractor(
            optional=optional,
            default_search_type=SearchType.case_insensitive,
            sequence_types=(list, set),
        )
        field_info, search_field_info = extractor(name, self.ModelTest.model_fields[name])
        assert field_info == res_field_info
        assert search_field_info == res_search_field_info
        
        
class TestFilterFieldExtractor:
    
    @staticmethod
    def type_definer_mock(target: str) -> Tuple[str, FilterType]:
        return target, FilterType.eq

    class ModelTest(BaseModel):
        f1: str
        f2: List[str]
        f3: str = FilterField()
        f4: str = ...
        f5: str = FilterField(...)
        f6: str = FilterField(le=1, ge=4, title="title")
        f7: str = FilterField(type_=FilterType.ne)
        f8: str = FilterField(target="f")

    @mock.patch.object(FieldInfo, "__eq__", new=partialmethod(__field_info_eq__, exclude=["annotation"]))
    @pytest.mark.parametrize(
        "name, optional, res_field_info, res_filter_field_info",
        [
            ("f1", True, Field(None), 
             FilterFieldInfo(target="f1", type_=FilterType.eq, is_sequence=False)),
            ("f1", False, Field(),
             FilterFieldInfo(target="f1", type_=FilterType.eq, is_sequence=False)),
            ("f2", True, Field(None),
             FilterFieldInfo(target="f2", type_=FilterType.eq, is_sequence=True)),
            ("f2", False, Field(),
             FilterFieldInfo(target="f2", type_=FilterType.eq, is_sequence=True)),
            ("f3", True, Field(None),
             FilterFieldInfo(target="f3", type_=FilterType.eq, is_sequence=False)),
            ("f3", False, Field(),
             FilterFieldInfo(target="f3", type_=FilterType.eq, is_sequence=False)),
            ("f4", True, Field(),
             FilterFieldInfo(target="f4", type_=FilterType.eq, is_sequence=False)),
            ("f4", False, Field(),
             FilterFieldInfo(target="f4", type_=FilterType.eq, is_sequence=False)),
            ("f5", True, Field(),
             FilterFieldInfo(target="f5", type_=FilterType.eq, is_sequence=False)),
            ("f5", False, Field(),
             FilterFieldInfo(target="f5", type_=FilterType.eq, is_sequence=False)),
            ("f6", True, Field(None, le=1, ge=4, title="title"),
             FilterFieldInfo(target="f6", type_=FilterType.eq, is_sequence=False)),
            ("f6", False, Field(le=1, ge=4, title="title"),
             FilterFieldInfo(target="f6", type_=FilterType.eq, is_sequence=False)),
            ("f7", True, Field(None), 
             FilterFieldInfo(target="f7", type_=FilterType.ne, is_sequence=False)),
            ("f8", True, Field(None), 
             FilterFieldInfo(target="f", type_=FilterType.eq, is_sequence=False)),
        ]
    )
    def test_call(
            self,
            name: str,
            optional: bool,
            res_field_info: FieldInfo,
            res_filter_field_info: FilterFieldInfo,
    ):
        extractor = FilterFieldExtractor(
            optional=optional,
            default_filter_type=FilterType.eq,
            sequence_types=(list, set),
            type_definer=self.type_definer_mock,
        )
        field_info, filter_field_info = extractor(name, self.ModelTest.model_fields[name])
        assert field_info == res_field_info
        assert filter_field_info == res_filter_field_info

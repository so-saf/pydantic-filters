from typing import List, Tuple

import pytest
from pydantic import ValidationError

from pydantic_filters import BaseFilter, FilterField, FilterType, SearchField, SearchType
from pydantic_filters.filter import _meta
    
    
def test_matching():
    class NestedFilter(BaseFilter):
        pass

    class TestFilter(BaseFilter):
        f1: str
        f2: List[str]
        f3: str = ...

        q1: str = SearchField(target=["f1"])
        q2: List[str] = SearchField(target=["f1"])

        n1: NestedFilter
        
    assert set(TestFilter.filter_fields.keys()) == {"f1", "f2", "f3"}
    assert set(TestFilter.search_fields.keys()) == {"q1", "q2"}
    assert set(TestFilter.nested_filters.keys()) == {"n1"}

    
def test_parent_fields():
    class NestedFilter(BaseFilter):
        pass
    
    class ParentFilter(BaseFilter):
        f1: str
        q1: str = SearchField(target=['f1'])
        n1: NestedFilter
        
    class ChildFilter(ParentFilter):
        f2: str
        q2: str = SearchField(target=['f2'])
        n2: NestedFilter

    assert set(ParentFilter.filter_fields.keys()) < set(ChildFilter.filter_fields.keys())
    assert set(ParentFilter.search_fields.keys()) < set(ChildFilter.search_fields.keys())
    assert set(ParentFilter.nested_filters.keys()) < set(ChildFilter.nested_filters.keys())


def test_child_metadata_does_not_mutate_parent_or_sibling():
    class ParentFilter(BaseFilter):
        parent: str

    class FirstChildFilter(ParentFilter):
        first: str

    class SecondChildFilter(ParentFilter):
        second: str

    assert set(ParentFilter.filter_fields) == {"parent"}
    assert set(FirstChildFilter.filter_fields) == {"parent", "first"}
    assert set(SecondChildFilter.filter_fields) == {"parent", "second"}


def test_child_can_override_inherited_field_metadata():
    class ParentFilter(BaseFilter):
        value: str

    class ChildFilter(ParentFilter):
        value: str = FilterField(target="renamed", type_=FilterType.ne)

    assert ParentFilter.filter_fields["value"].target == "value"
    assert ParentFilter.filter_fields["value"].type is FilterType.eq
    assert ChildFilter.filter_fields["value"].target == "renamed"
    assert ChildFilter.filter_fields["value"].type is FilterType.ne


def test_default_optional_config_allows_an_empty_filter():
    class OptionalFilter(BaseFilter):
        value: int

    filter_ = OptionalFilter()

    assert filter_.value is None
    assert filter_.model_dump(exclude_unset=True) == {}


def test_explicit_ellipsis_keeps_all_field_kinds_required():
    class NestedFilter(BaseFilter):
        value: int

    class ExplicitFilter(BaseFilter):
        implicit: int
        plain: int = ...
        filtered: int = FilterField(...)
        searched: str = SearchField(..., target=["plain"])
        nested: NestedFilter = ...

    assert ExplicitFilter.model_fields["implicit"].is_required() is False
    assert all(
        ExplicitFilter.model_fields[name].is_required()
        for name in ("plain", "filtered", "searched", "nested")
    )


def test_optional_false_keeps_fields_required():
    class RequiredFilter(BaseFilter):
        model_config = {**BaseFilter.model_config, "optional": False}
        value: int

    with pytest.raises(ValidationError, match="value"):
        RequiredFilter()


def test_custom_delimiter_and_suffix_map_define_target_and_operator():
    class CustomFilter(BaseFilter):
        model_config = {
            **BaseFilter.model_config,
            "delimiter": "___",
            "suffixes_map": {"before": FilterType.lt},
        }
        created_at___before: int

    field = CustomFilter.filter_fields["created_at___before"]
    assert field.target == "created_at"
    assert field.type is FilterType.lt


def test_custom_sequence_types_are_used_by_filter_and_search_fields():
    class TupleFilter(BaseFilter):
        model_config = {**BaseFilter.model_config, "sequence_types": (list, set, tuple)}
        values: Tuple[int, ...]
        query: Tuple[str, ...] = SearchField(target=["name"])

    assert TupleFilter.filter_fields["values"].is_sequence is True
    assert TupleFilter.search_fields["query"].is_sequence is True


def test_custom_default_types_do_not_mutate_base_config():
    class CustomFilter(BaseFilter):
        model_config = {
            **BaseFilter.model_config,
            "default_filter_type": FilterType.ne,
            "default_search_type": SearchType.case_sensitive,
        }
        value: int
        query: str = SearchField(target=["value"])

    assert CustomFilter.filter_fields["value"].type is FilterType.ne
    assert CustomFilter.search_fields["query"].type is SearchType.case_sensitive
    assert BaseFilter.model_config["default_filter_type"] is FilterType.eq
    assert BaseFilter.model_config["default_search_type"] is SearchType.case_insensitive


def test_annotationlib_branch_reads_class_namespace(monkeypatch):
    class FakeAnnotationLib:
        calls = []

        class Format:
            FORWARDREF = object()

        @classmethod
        def get_annotate_from_class_namespace(cls, namespace):
            cls.calls.append("get")
            assert "__annotations__" in namespace or "__annotate_func__" in namespace
            return {"value": int}

        @classmethod
        def call_annotate_function(cls, annotate, format_):
            cls.calls.append(("call", format_))
            return annotate

    monkeypatch.setattr(_meta, "annotationlib", FakeAnnotationLib)

    class AnnotationLibFilter(BaseFilter):
        value: int

    assert set(AnnotationLibFilter.filter_fields) == {"value"}
    assert FakeAnnotationLib.calls == [
        "get",
        ("call", FakeAnnotationLib.Format.FORWARDREF),
    ]


def test_annotationlib_branch_allows_a_class_without_annotations(monkeypatch):
    class FakeAnnotationLib:
        class Format:
            FORWARDREF = object()

        @staticmethod
        def get_annotate_from_class_namespace(namespace):
            return None

        @staticmethod
        def call_annotate_function(annotate, format_):
            raise AssertionError("No annotation function should be called")

    monkeypatch.setattr(_meta, "annotationlib", FakeAnnotationLib)

    class EmptyFilter(BaseFilter):
        pass

    assert EmptyFilter.filter_fields == {}

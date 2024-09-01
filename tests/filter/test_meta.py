from typing import List

from pydantic_filters import BaseFilter, SearchField
    
    
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

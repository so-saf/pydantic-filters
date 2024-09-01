from typing import Any, Dict

import pytest
import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic_filters import FilterType, SearchType
from pydantic_filters.drivers.sqlalchemy._operators import (
    _op_from_method,
    _op_eq,
    _op_ne,
    _op_null,
    _op_case_sensitive_search,
    _op_case_insensitive_search,
    _filter_type_to_operator_map,
    _search_type_to_operator_map,
)


class Base(so.DeclarativeBase):
    pass


class ModelTest(Base):
    __tablename__ = 'tests'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)


@pytest.mark.parametrize(
    "method, is_sequence, item, res_clause", 
    [
        ("__eq__", False, 1, ModelTest.id == 1),
        ("__ne__", False, 1, ModelTest.id != 1),
        ("__eq__", True, [1, 2], sa.or_(ModelTest.id == 1, ModelTest.id == 2))
    ]
)
def test_op_from_method_for_no_sequence(
        method: str, is_sequence: bool, item: Any, res_clause: sa.BinaryExpression[bool],
):
    operator = _op_from_method(method)
    clauses = operator(ModelTest.id, is_sequence, item)
    assert clauses.compare(res_clause)


@pytest.mark.parametrize(
    "is_sequence, obj, res_clause",
    [
        (False, 1, ModelTest.id == 1),
        (True, [1, 2], ModelTest.id.in_([1, 2])),
    ]
)
def test_op_eq(is_sequence: bool, obj: Any, res_clause: sa.BinaryExpression[bool]):
    clause = _op_eq(ModelTest.id, is_sequence, obj)
    assert clause.compare(res_clause)

 
@pytest.mark.parametrize(
    "is_sequence, obj, res_clause",
    [
        (False, 1, ModelTest.id != 1,),
        (True, [1, 2], ModelTest.id.not_in([1, 2])),
    ]
)
def test_op_ne(is_sequence: bool, obj: Any, res_clause: sa.BinaryExpression[bool]):
    clause = _op_ne(ModelTest.id, is_sequence, obj)
    assert clause.compare(res_clause)
        
        
@pytest.mark.parametrize(
    "is_sequence, obj, res_clause",
    [
        (False, True, ModelTest.id.is_(None)),
        (False, 1, ModelTest.id.is_(None)),
        (False, False, ModelTest.id.is_not(None)),
        (False, 0, ModelTest.id.is_not(None)),
        (True, [False, False], ModelTest.id.is_not(None)),
        (True, [0, ''], ModelTest.id.is_not(None)),
        (True, [True, False], ModelTest.id.is_(None)),
        (True, ['1', ''], ModelTest.id.is_(None)),
        (True, [True, True], ModelTest.id.is_(None)),
        (True, [1, '1'], ModelTest.id.is_(None)),
    ]
)
def test_op_null(is_sequence: bool, obj: Any, res_clause: sa.BinaryExpression[bool]):
    clause = _op_null(ModelTest.id, is_sequence, obj)
    assert clause.compare(res_clause)
    

@pytest.mark.parametrize(
    "is_sequence, obj, res_clause",
    [
        (False, "a", ModelTest.id.like("%a%")),
        (False, 1, ModelTest.id.like("%1%")),
        (True, ["a", "b"], sa.or_(ModelTest.id.like("%a%"), ModelTest.id.like("%b%"))),
    ]
)
def test_op_case_sensitive_search(is_sequence: bool, obj: Any, res_clause: sa.BinaryExpression[bool]):
    clause = _op_case_sensitive_search(ModelTest.id, is_sequence, obj)
    assert clause.compare(res_clause)
    
    
@pytest.mark.parametrize(
    "is_sequence, obj, res_clause",
    [
        (False, "a", ModelTest.id.ilike("%a%")),
        (False, 1, ModelTest.id.ilike("%1%")),
        (True, ["a", "b"], sa.or_(ModelTest.id.ilike("%a%"), ModelTest.id.ilike("%b%"))),
    ]
)
def test_op_case_insensitive_search(is_sequence: bool, obj: Any, res_clause: sa.BinaryExpression[bool]):
    clause = _op_case_insensitive_search(ModelTest.id, is_sequence, obj)
    assert clause.compare(res_clause)
    

@pytest.mark.parametrize(
    "map_, enum",
    [
        (_filter_type_to_operator_map, FilterType),
        (_search_type_to_operator_map, SearchType),
    ]
)
def test_fullness_map(map_: Dict, enum):
    assert set(map_.keys()) == set(enum)

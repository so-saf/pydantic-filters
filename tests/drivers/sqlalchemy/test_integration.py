from typing import List, Optional

import sqlalchemy as sa
import sqlalchemy.orm as so

from pydantic_filters import BaseFilter, BaseSort, FilterField, OffsetPagination, SearchField, SortByOrder
from pydantic_filters.drivers.sqlalchemy import append_to_statement, get_count_statement


class Base(so.DeclarativeBase):
    pass


user_role = sa.Table(
    "user_role",
    Base.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("role_id", sa.ForeignKey("roles.id"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str]


class User(Base):
    __tablename__ = "users"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str]
    roles: so.Mapped[List[Role]] = so.relationship(secondary=user_role)


class Employee(Base):
    __tablename__ = "employees"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    manager_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey("employees.id"))
    manager: so.Mapped[Optional["Employee"]] = so.relationship(remote_side="Employee.id")


class CompositeParent(Base):
    __tablename__ = "composite_parents"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    tenant_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str]


class CompositeChild(Base):
    __tablename__ = "composite_children"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    parent_id: so.Mapped[int]
    tenant_id: so.Mapped[int]
    parent: so.Mapped[CompositeParent] = so.relationship()
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["parent_id", "tenant_id"],
            ["composite_parents.id", "composite_parents.tenant_id"],
        ),
    )


class Item(Base):
    __tablename__ = "items"
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str]
    score: so.Mapped[int]


class RoleFilter(BaseFilter):
    name: str


class UserFilter(BaseFilter):
    roles: RoleFilter


class TopManagerFilter(BaseFilter):
    id: int


class ManagerFilter(BaseFilter):
    manager: TopManagerFilter


class EmployeeFilter(BaseFilter):
    manager: ManagerFilter


class CompositeParentFilter(BaseFilter):
    name: str


class CompositeChildFilter(BaseFilter):
    parent: CompositeParentFilter


class ItemFilter(BaseFilter):
    id: List[int]
    id__n: List[int]
    score__ge: int
    query: List[str] = SearchField(target=["name"])


def make_session() -> so.Session:
    engine = sa.create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return so.Session(engine)


def test_many_to_many_nested_filter_executes_against_secondary_table() -> None:
    with make_session() as session:
        admin = Role(id=1, name="admin")
        reader = Role(id=2, name="reader")
        session.add_all([
            User(id=1, name="Alice", roles=[admin]),
            User(id=2, name="Bob", roles=[reader]),
        ])
        session.commit()

        statement = append_to_statement(
            sa.select(User),
            User,
            filter_=UserFilter(roles=RoleFilter(name="admin")),
        )

        assert session.scalars(statement).all() == [session.get(User, 1)]


def test_composite_foreign_key_uses_every_local_remote_pair() -> None:
    with make_session() as session:
        selected = CompositeParent(id=1, tenant_id=10, name="selected")
        other = CompositeParent(id=1, tenant_id=20, name="other")
        session.add_all([
            selected,
            other,
            CompositeChild(id=1, parent_id=1, tenant_id=10, parent=selected),
            CompositeChild(id=2, parent_id=1, tenant_id=20, parent=other),
        ])
        session.commit()

        statement = append_to_statement(
            sa.select(CompositeChild),
            CompositeChild,
            filter_=CompositeChildFilter(parent=CompositeParentFilter(name="selected")),
        )

        assert [child.id for child in session.scalars(statement)] == [1]


def test_multiple_self_referential_levels_use_distinct_aliases() -> None:
    with make_session() as session:
        ceo = Employee(id=1)
        manager = Employee(id=2, manager=ceo)
        employee = Employee(id=3, manager=manager)
        unrelated = Employee(id=4)
        session.add_all([ceo, manager, employee, unrelated])
        session.commit()

        statement = append_to_statement(
            sa.select(Employee),
            Employee,
            filter_=EmployeeFilter(manager=ManagerFilter(manager=TopManagerFilter(id=1))),
        )

        assert session.scalars(statement).all() == [employee]


def test_filter_sort_pagination_and_count_execute_together() -> None:
    with make_session() as session:
        session.add_all([
            Item(id=1, name="first", score=10),
            Item(id=2, name="second", score=20),
            Item(id=3, name="third", score=30),
        ])
        session.commit()
        filter_ = ItemFilter(score__ge=10)

        statement = append_to_statement(
            sa.select(Item),
            Item,
            filter_=filter_,
            sort=BaseSort(sort_by="score", sort_by_order=SortByOrder.desc),
            pagination=OffsetPagination(limit=1, offset=1),
        )

        assert session.scalars(statement).all() == [session.get(Item, 2)]
        assert session.scalar(get_count_statement(Item, filter_)) == 3


def test_empty_equality_sequence_matches_nothing() -> None:
    with make_session() as session:
        session.add(Item(id=1, name="first", score=10))
        session.commit()

        statement = append_to_statement(sa.select(Item), Item, filter_=ItemFilter(id=[]))

        assert session.scalars(statement).all() == []


def test_empty_inequality_sequence_matches_everything() -> None:
    with make_session() as session:
        item = Item(id=1, name="first", score=10)
        session.add(item)
        session.commit()

        statement = append_to_statement(sa.select(Item), Item, filter_=ItemFilter(id__n=[]))

        assert session.scalars(statement).all() == [item]


def test_empty_search_sequence_matches_nothing() -> None:
    with make_session() as session:
        session.add(Item(id=1, name="first", score=10))
        session.commit()

        statement = append_to_statement(sa.select(Item), Item, filter_=ItemFilter(query=[]))

        assert session.scalars(statement).all() == []

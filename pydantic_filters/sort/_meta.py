from typing import TYPE_CHECKING, Any, Dict, Tuple, Type, cast

from pydantic._internal._model_construction import ModelMetaclass as _ModelMetaclass  # noqa: PLC2701
from pydantic.fields import FieldInfo

if TYPE_CHECKING:
    from .base import BaseSort


class SortMetaclass(_ModelMetaclass):

    def __new__(
            mcs,  # noqa: N804
            name: str,
            bases: Tuple[Type[Any], ...],
            namespace: Dict[str, Any],
            **kwargs,  # noqa: ANN003
    ) -> Type["BaseSort"]:
        sort_class = cast(Type["BaseSort"], super().__new__(mcs, name, bases, namespace, **kwargs))

        for field_name, field_info in sort_class.model_fields.items():
            if field_info.is_required():
                namespace[field_name] = FieldInfo.merge_field_infos(field_info, default=None)

        return cast(Type["BaseSort"], super().__new__(mcs, name, bases, namespace, **kwargs))

import re
from typing import Dict, Tuple

from pydantic_filters.filter._types import FilterType

_DELIMITER_REGEX = re.compile(r"^_{2,}$")


class FilterTypeDefiner:
    """Define field filter type by the suffix

    **Example**

    >>> definer = FilterTypeDefiner(
    ...    delimiter="__",
    ...    default=FilterType.eq,
    ...    suffixes_map={"neq": FilterType.ne},
    ... )
    >>> definer("name__neq")
    ('name', <FilterTypes.neq: 'not_equal'>)
    """

    def __init__(
            self,
            delimiter: str,
            default: FilterType,
            suffixes_map: Dict[str, FilterType],
    ) -> None:
        if not _DELIMITER_REGEX.match(delimiter):
            raise ValueError("delimiter must be specified")

        self.delimiter = delimiter
        self.default = default
        self.suffixes_map = suffixes_map

    def __call__(self, target: str) -> Tuple[str, FilterType]:
        """
        :return: Defined name and filter type
        """

        divided = target.rsplit(self.delimiter, maxsplit=1)
        if len(divided) == 1:
            return target, self.default

        suffix = divided[-1]
        try:
            type_ = self.suffixes_map[suffix]
        except KeyError:
            return target, self.default

        return divided[0], type_

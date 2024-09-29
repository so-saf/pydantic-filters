Sorting determines in what order the data is selected. 
There is a [`BaseSort`][pydantic_filters.BaseSort] class for this purpose. 
It can be used in its “raw” form or by adding your own metadata:

```python
from typing import Optional
from enum import Enum

from pydantic_filters import BaseSort


class UserOrderByEnum(str, Enum):
    id = "id"
    login = "login"
    full_name = "full_name"
    
    
class UserSort(BaseSort):
    sort_by: Optional[UserOrderByEnum] = None
```

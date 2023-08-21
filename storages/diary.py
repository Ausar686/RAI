# Created by: Ausar686
# https://github.com/Ausar686

from typing import Union, Any

from pandas.core.frame import DataFrame

from .base_storage import BaseStorage


class Diary(BaseStorage):
    
    def __init__(self, df: Union[DataFrame,str]=None):
        self._columns = ["emotion", "reason", "text", "media"]
        self._indexed_columns = ["emotion", "reason", "media"]
        self._multivalue_columns = ["emotion", "reason"]
        super().__init__(df)
        return
    
    def get(self, 
            *, 
            by: str, 
            value: Any=None, 
            search_type: str="union", 
            date_search: str="precise") -> DataFrame:
        ret, data = self._base_get(
            by=by,
            value=value,
            search_type=search_type,
            date_search=date_search)
        if ret:
            return data
        if by == "emotion":
            return self._substr_search(by, value)
        elif by == "reason":
            return self._substr_search(by, value)
        elif by == "media":
            return self._eq_search(by, value)
        else:
            raise ValueError("Invalid search argument.")
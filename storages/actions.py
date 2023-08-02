from typing import Union, Any

from pandas.core.frame import DataFrame

from .base_storage import BaseStorage


class Actions(BaseStorage):
    
    def __init__(self, df: Union[DataFrame,str]=None):
        self._columns = ["media", "author", "title", "topic", "duration", "text"]
        self._indexed_columns = ["media", "author", "title", "topic"]
        self._multivalue_columns = ["topic"]
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
        if by == "media":
            return self._eq_search(by, value)
        elif by == "author":
            return self._eq_search(by, value)
        elif by == "title":
            return self._eq_search(by, value)
        elif by == "topic":
            return self._substr_search(by, value)
        else:
            raise ValueError("Invalid search argument.")
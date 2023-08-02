from typing import Any, Union, Tuple, Iterable
from datetime import datetime

import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.series import Series


class BaseStorage:
    _base_columns = ["date", "time", "datetime"]
    _base_indexed_columns = ["date"]
    _base_multivalue_columns = []
    _columns = []
    _indexed_columns = []
    _multivalue_columns = []
    
    def __init__(self, df: Union[DataFrame,str]=None):
        self._index_col = "index"
        self._columns.extend(self._base_columns)
        self._indexed_columns.extend(self._base_indexed_columns)
        self._multivalue_columns.extend(self._base_multivalue_columns)
        if df is None:
            self.data = pd.DataFrame(columns=self._columns)
            return
        elif isinstance(df, str):
            self.from_csv(df)
        else:
            self.data = df.copy()
        extra_columns = [column for column in self.data.columns if column not in self._columns]
        self.data.drop(extra_columns, axis=1, inplace=True)
        for column in self._columns:
            if column == "datetime":
                self.data["datetime"] = pd.to_datetime(self.data["date"] + ' ' + self.data["time"])
            if column not in self.data.columns:
                self.data[column] = None
        return
    
    def create(self, dct: dict) -> dict:
        note = {key: self.iter_to_str(value) if key in self._multivalue_columns
                else value for key, value in dct.items()}
        now = datetime.now()
        note["date"] = now.date().strftime("%Y-%m-%d")
        note["time"] = now.time().strftime("%H:%M")
        note["datetime"] = note["date"] + ' ' + note["time"]
        return note
    
    def add(self, note: dict) -> None:
        new_row = pd.Series(note)
        try:
            index = self.data.index[-1] + 1
        except IndexError:
            index = 0
        self.data.loc[index] = new_row
        return
    
    def append(self, dct: dict) -> None:
        # A convinient way to add a new note from the dict to the storage.
        # This method consequently performs 'create' and 'add' methods.
        note = self.create(dct)
        self.add(note)
        return
    
    def delete(self, index: int) -> None:
        try:
            self.data.drop(index, inplace=True)
        except KeyError:
            print(f"[INFO]: No row with index {index} found. Ignored.")
        return
    
    def edit(self, index: int=None, note: Union[dict, Series]=None) -> None:
        if index is None and note is None:
            return
        # If index is None, we are trying to edit a specific row, metioned in note
        if index is None: 
            index = note.name
        if index not in self.data.index:
            print(f"[INFO]: No row with index {index} found. Ignored.")
            return
        for key in note:
            if key not in self._columns:
                continue
            value = note[key]
            if key in self._multivalue_columns and self.is_nonstr_iterable(value):
                value = self.iter_to_str(value)
            self.data.loc[index, key] = value
        return
    
    def _base_get(self, 
                  *, 
                  by: str,
                  value: Any=None,
                  search_type: str="union",
                  date_search: str="precise") -> Tuple[bool, Union[DataFrame, Series]]:
        # Performs basic search, which is similar to all subclasses.
        # 'value' is not specified. Return all data 
        if value is None:
            return True, self.data
        # Search by index via 'loc' method
        elif by == "index":
            return True, self.data.loc[value]
        elif by == "date":
            if date_search == "precise":
                return True, self._eq_search(by, value)
            elif date_search == "between":
                date_start = value[0]
                date_end = value[1]
                return True, self._date_search(date_start, date_end)
            else:
                raise ValueError("Parameter 'date_search' must be either 'precise' or 'between'.")
        # 'by' is either a string or non-iterable object
        # and 'value' is a non-string iterable object
        elif not self.is_nonstr_iterable(by) and self.is_nonstr_iterable(value):
            if search_type not in ["union", "intersection"]:
                raise ValueError("Parameter 'search_type' must be either 'union' or 'intersection'.")
            res_idx = None
            for i, value_ in enumerate(value):
                # Iterate over values in 'value'
                # And apply index union/intersection among results
                # The type of operation depends on 'search_type' parameter
                current_res = self.get(by=by, value=value_)
                if i == 0:
                    res_idx = current_res.index
                else:
                    res_idx = res_idx.__getattribute__(search_type)(current_res.index)
            # Return rows with indexes in 'res_idx'
            return True, self.data.loc[res_idx]
        elif self.is_nonstr_iterable(by):
            # Group arguments into pairs column-value
            pairs = zip(by, value)
            res_idx = None
            for i, pair in enumerate(pairs):
                # Iterate over pairs in zip
                # And apply index intersection among results
                by_, value_ = pair
                current_res = self.get(by=by_, value=value_)
                if i == 0:
                    res_idx = current_res.index
                else:
                    res_idx = res_idx.intersection(current_res.index)
            # Return rows with indexes in 'res_idx'
            return True, self.data.loc[res_idx]
#             raise NotImplementedError("Multiple search will be implemented in upcoming updates.")
        elif by not in self._indexed_columns:
            raise ValueError("Invalid search argument.")
        return False, None
            
    def _eq_search(self, column: str, value: Any) -> DataFrame:
        # Columnwise equality-based search.
        return self.data[self.data[column]==value]
    
    def _substr_search(self, column: str, value: Any) -> DataFrame:
        # Return all rows, where the following column cell
        return self.data[self.data[column].str.contains(value)]
    
    def _date_search(self, date_start: str, date_end: str):
        # Return all rows, where date is in between 'date_start' and 'date_end'
        return self.data[(date_start <= self.data.date) & (self.data.date <= date_end)]
    
    def get(self, 
            *,
            by: str,
            value: Any=None,
            search_type: str="union",
            date_search: str="precise") -> DataFrame:
        # Define a 'get' method for subclasses.
        # Implementation depends on a specific subclass.
        # It is strongly recommended to use '_base_get' method
        # in the beginning of 'get' method in any subclass
        pass
    
    @staticmethod
    def is_iterable(obj: Any) -> bool:
        try:
            iter(obj)
            return True
        except TypeError:
            return False
        
    @classmethod
    def is_nonstr_iterable(cls, obj: Any) -> bool:
        return cls.is_iterable(obj) and not isinstance(obj, str)
    
    @classmethod
    def iter_to_str(cls, lst: Iterable[str]) -> str:
        if cls.is_nonstr_iterable(lst):
            return '|'.join(lst)
        return lst

    def from_csv(self, path: str) -> None:
        self.data = pd.read_csv(path, index_col=self._index_col)
        return
    
    def to_csv(self, path: str) -> None:
        self.data.drop_duplicates(self._columns, keep="last").to_csv(path, index_label=self._index_col)
        return
    
    def load(self, path: str) -> None:
        # An alias for 'from_csv' method for standartized interface
        self.from_csv(path)
        return
    
    def to_disk(self, path: str) -> None:
        # An alias for 'to_csv' method for standartized interface
        self.to_csv(path)
        return
        
    def __repr__(self):
        return repr(self.data)
    
    def __str__(self):
        return str(self.data)
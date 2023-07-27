from typing import Any, Union
from datetime import datetime

import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.series import Series


class Diary:
    _columns = ["date", "time", "emotion", "reason", "text", "media"]
    
    def __init__(self, df: Union[DataFrame,str]=None) -> None:
        if df is None:
            self.data = pd.DataFrame(columns=self._columns)
            return
        if isinstance(df, str):
            self.from_csv(df)
        else:
            self.data = df.copy()
        extra_columns = [column for column in self.data.columns if column not in self._columns]
        self.data.drop(extra_columns, axis=1, inplace=True)
        for column in self._columns:
            if column not in self.data.columns:
                self.data[column] = None
        return
    
    @staticmethod
    def create_note(dct: dict) -> dict:
        note = dict(dct)
        now = datetime.now()
        note["date"] = now.date().strftime("%Y-%m-%d")
        note["time"] = now.time().strftime("%H:%M")
        return note
    
    def add_note(self, note: dict) -> None:
        new_row = pd.Series(note)
        self.data.loc[self.data.shape[0]] = new_row
        return
    
    def del_note(self, index: int) -> None:
        try:
            self.data.drop(index, inplace=True)
        except KeyError:
            print(f"[INFO]: No row with index {index} found. Ignored.")
        return
    
    def edit_note(self, index: int=None, note: Union[dict, Series]=None) -> None:
        if index is None and note is None:
            return
        # We are trying to edit a specific row, metioned in note
        if index is None: 
            index = note.name
        if index not in self.data.index:
            print(f"[INFO]: No row with index {index} found. Ignored.")
            return
        for key in note:
            if key not in self._columns:
                continue
            value = note[key]
            self.data.loc[index, key] = value
        return
    
    def get_notes(self, *, by: str, value: Any=None) -> pd.DataFrame:
        if value is None:
            return self.data
        if self.is_iterable(by) and not isinstance(by, str):
            raise NotImplementedError("Multiple search will be implemented in upcoming updates.")
        if by == "date":
            return self.data[self.data.date==value]
        elif by == "emotion":
            return self.data[self.data.emotion.str.contains(value)]
        elif by == "reason":
            return self.data[self.data.reason.str.contains(value)]
        elif by == "media":
            return self.data[self.data.media==value]
        else:
            raise ValueError("Invalid search argument.")
            
    @staticmethod
    def is_iterable(obj: Any) -> bool:
        try:
            iter(obj)
            return True
        except TypeError:
            return False

    def to_csv(self, path: str) -> None:
        self.data.to_csv(path, index=False)
        return

    def from_csv(self, path: str) -> None:
        self.data = pd.read_csv(path)
        return
        
    def __repr__(self):
        return repr(self.data)
    
    def __str__(self):
        return str(self.data)
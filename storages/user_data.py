from typing import Union, Any
import json
from collections import defaultdict


class UserData:
    _attributes = ["first_name", "last_name", "username", "_fav_topics", "_fav_diary_topics", "_fav_actions_topics"]
    
    def __init__(self, data: Union[str, dict]=None):
        if data is None:
            self.from_empty()
            return
        elif isinstance(data, str):
            self.from_json(data)
            return
        elif isinstance(data, dict):
            self.from_dict(data)
            return
        else:
            raise TypeError(f"Can't initialize UserData object from type {type(data)}"
                           "Supported types are: str, dict.")
    
    def from_json(self, path: str):
        with open(path, "r", encoding="utf-8") as json_file:
            dct = json.load(json_file)
        self.from_dict(dct)
        return
    
    def from_empty(self) -> None:
        for attr in self._attributes:
            if attr[0] == "_":
                self.__setattr__(attr, defaultdict(float))
            else:
                self.__setattr__(attr, None)
        return
    
    def from_dict(self, dct: dict) -> None:
        for attr in self._attributes:
            if attr in dct:
                if attr[0] == "_":
                    self.__setattr__(attr, defaultdict(float, dct[attr]))
                else:
                    self.__setattr__(attr, dct[attr])
            else:
                if attr[0] == "_":
                    self.__setattr__(attr, defaultdict(float))
                else:
                    self.__setattr__(attr, None)
        return
    
    @property
    def dict(self) -> dict:
        return {attr: self.__getattribute__(attr) for attr in self._attributes}
    
    def to_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as json_file:
            json.dump(self.dict, json_file)
        return
    
    def __getitem__(self, item: str) -> Any:
        # An alias for __getattribute__.
        return self.__getattribute__(item)
    
    def load(self, path: str) -> None:
        # An alias for 'from_json' for standartized interface
        self.from_json(path)
        return
    
    def to_disk(self, path: str) -> None:
        # An alias for 'to_json' for standartized interface
        self.to_json(path)
        return
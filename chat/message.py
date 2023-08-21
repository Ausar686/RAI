# Created by: Ausar686
# https://github.com/Ausar686

from typing import Union, Any
from datetime import datetime
import json


class Message:
    """
    Class, that implements messages in chat.
    """
    
    _attributes = ["content", "role", "username", "chat_id", "date", "time", 
                   "is_reply", "reply", "is_forward", "forward", "media"]
    _bot_data = ['role', 'content']
    _front_keys = ["content", "role", "username", "date", "time"]
    
    def __init__(self, content: Union[str,dict,"Message"]=None):
        """
        Initializes an instance of a class.
        Args:
            content: Union[str,dict,Message]: Message content. Default: None
        """
        if isinstance(content, dict):
            self.from_dict(content)
            return
        elif isinstance(content, str):
            self.from_str(content)
            return
        elif isinstance(content, Message):
            self.from_message(content)
        else:
            raise TypeError("Parameter 'content' must be either str or dict.")
    
    def from_dict(self, dct: dict) -> None:
        for attr in self._attributes:
            self.__setattr__(attr, dct.get(attr))
        self.set_datetime()
        return
    
    def from_str(self, content: str) -> None:
        for attr in self._attributes:
            self.__setattr__(attr, None)
        self.content = content
        self.role = "user"
        self.set_datetime()
        return
    
    def from_message(self, message: "Message"=None) -> None:
        self.from_dict(message.to_dict)
        return
    
    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as json_file:
            json_message = json.load(json_file)
        self.from_dict(json_message)
        return
    
    def set_datetime(self) -> None:
        if self.date is None or self.time is None:
            now = datetime.now()
            self.date = now.date().strftime("%Y-%m-%d")
            self.time = now.time().strftime("%H:%M")
        return
    
    def to_openai(self) -> dict:
        return {key: self[key] for key in self._bot_data}
    
    def to_dict(self) -> dict:
        return {key: self[key] for key in self._attributes}
    
    def to_front(self) -> dict:
        return {key: self[key] for key in self._front_keys}
    
    def get(self, key: str) -> Any:
        return self.to_dict().get(key)
            
    def __delitem__(self, item: str) -> None:
        raise KeyError("Access denied.")
            
    def __setitem__(self, item: str, value: Any) -> None:
        self.__setattr__(item, value)
        
    def __getitem__(self, item: str) -> Any:
        return self.__getattribute__(item)
        
    def __delattr__(self, attr: str) -> None:
        raise AttributeError("Access denied.")
    
    def __len__(self) -> int:
        return len(self.content)
    
    def __add__(self, other: Any) -> str:
        return self.content + str(other)
    
    def __radd__(self, other: Any) -> str:
        return self.__add__(other)
    
    def __iadd__(self, other: Any):
        self.content += str(other)
        return self
    
    def __eq__(self, other: Any) -> bool:
        return self.content == str(other)
    
    def __neq__(self, other: Any) -> bool:
        return not self.__eq__(other)
            
    def __repr__(self):
        return str(self.__dict__)
    
    def __str__(self):
        return self.content
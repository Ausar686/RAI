# Created by: Ausar686
# https://github.com/Ausar686

from typing import Union
from datetime import datetime
import os
import hashlib
import copy
import json

from .message import Message


class Chat:
    
    _image_dir = "bot_images"
    _data_dir = "chats"
    _default_name = "chat"
    _chunk_size = 100
    _suffix_len = 7
    _attributes = ["username", "bot_name", "messages", "recent_messages", "image"]
    _names = ["username", "bot_name"]
    _db_columns = ["chat_id", "role", "content", "date", "time"]
    _db_table = "messages"
    
    def __init__(self, load_data: Union[str,dict]=None):
        if isinstance(load_data, str):
            self.from_path(load_data)
            return
        elif isinstance(load_data, dict):
            self.from_dict(load_data)
            return
        else:
            raise TypeError("Parameter 'load_data' must be either dict or str.")
    
    def from_dict(self, dct: dict) -> None:
        for attr in self._attributes:
            if attr == "messages":
                self.__setattr__(attr, copy.deepcopy(dct.get(attr)))
                if self.messages is None:
                    self.messages = []
            elif attr == "recent_messages":
                self.recent_messages = []
            else:
                self.__setattr__(attr, dct.get(attr))
        for name in self._names:
            if self.__getattribute__(name) is None:
                raise ValueError("Username and bot name must be not None.")
        self.chat_id = self.make_id()
        for message in self.messages:
            self.set_message_data(message, setup_datetime=False)
        self.image = self.get_image_path()
        return
    
    def from_path(self, load_dir: str=None) -> None:
        if load_dir is None:
            raise ValueError("Directory must be not None.")
        if not os.path.exists(load_dir):
            raise ValueError("Directory does not exist.")
        load_dir = os.sep.join(load_dir.split('/'))
        self.bot_name = load_dir.split(os.sep)[-1]
        self.username = load_dir.split(os.sep)[-2]
        self.chat_id = self.make_id()
        self.messages = []
        self.recent_messages = []
        for filename in os.listdir(load_dir):
            path = os.path.join(load_dir, filename)
            with open(path, "r", encoding="utf-8") as json_file:
                json_messages = json.load(json_file)
            messages = [Message(json_message) for json_message in json_messages]
            self.messages.extend(messages)
        for message in self.messages:
            self.set_message_data(message, setup_datetime=False)
        self.image = self.get_image_path()
        return
    
    def get_image_path(self) -> str:
        return os.path.join(self._image_dir, f"{self.bot_name}.jpg")
    
    def make_id(self) -> str:
        # Returns an id of the chat by hashing data
        return hashlib.sha256((f"{self.username}###{self.bot_name}").encode()).hexdigest()
    
    def set_message_data(self, message: Message=None, setup_datetime: bool=True) -> None:
        if message is None:
            return
        if message.role == "assistant":
            message.username = self.bot_name
        elif message.role == "user":
            message.username = self.username
        else:
            message.username = "ROOT"
        message.chat_id = self.chat_id
        if setup_datetime:
            now = datetime.now()
            message.date = now.date().strftime("%Y-%m-%d")
            message.time = now.time().strftime("%H:%M")
        return
        
    def append(self, message: Union[Message,dict]=None) -> None:
        if message is None:
            return
        if isinstance(message, dict):
            message = Message(message)
        self.set_message_data(message)
        self.messages.append(message)
        self.recent_messages.append(message)
        return
    
    @property
    def last(self) -> Message:
        if self.messages:
            return self.messages[-1]
        return None
    
    def to_front(self) -> dict:
        if self.last is not None:
            front_dict = self.last.to_front()
            front_dict["image"] = self.image
            return {self.bot_name: front_dict}
        else:
            return {self.bot_name: {key: None for key in Message._front_keys}}
        
    def to_database(self):
        # TODO: Write actual code for this
        # TODO: Make this method async
        # Sends messages to database
        self.recent_messages.clear()
        return
        
    def __len__(self) -> int:
        return len(self.messages)
    
    def __iter__(self):
        return iter(self.messages)
    
    def __getitem__(self, item: int) -> Message:
        return self.messages[item]
        
    def load(self, load_dir: str=None) -> None:
        # An alias for 'from_path' method for standartized interface
        self.from_path(load_dir)
        return
    
    def to_disk(self) -> None:
        output_dir = self._data_dir
        # if not os.path.exists(output_dir):
            # raise ValueError("Directory does not exist.")
        output_user_dir = os.path.join(output_dir, self.username)
        # if not os.path.exists(output_user_dir):
        #     os.mkdir(output_user_dir)
        output_bot_dir = os.path.join(output_user_dir, self.bot_name)
        if not os.path.exists(output_bot_dir):
            os.makedirs(output_bot_dir)
        splitted_messages = []
        for i in range(0, len(self), self._chunk_size):
            chunk = [message.to_dict() for message in self.messages[i: i+self._chunk_size]]
            splitted_messages.append(chunk)
        for i, chunk in enumerate(splitted_messages):
            suffix = str(i).zfill(self._suffix_len)
            filename = f"{self._default_name}{suffix}.json"
            path = os.path.join(output_bot_dir, filename)
            with open(path, "w", encoding="utf-8") as json_file:
                json.dump(chunk, json_file)
        return
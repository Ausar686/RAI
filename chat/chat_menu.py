# Created by: Ausar686
# https://github.com/Ausar686

from typing import Iterable, List
from collections import deque

from .chat import Chat


class ChatMenu:
    
    def __init__(self, chats: Iterable[Chat]=None):
        if chats is None:
            self.chats = deque()
        else:
            self.chats = deque(chats)
        return
    
    def __getitem__(self, item: int) -> Chat:
        return self.chats[item]
    
    def to_front(self) -> List[dict]:
        return [chat.to_front() for chat in self.chats]
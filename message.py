from datetime import datetime
from typing import List, Any

from .media import BaseMedia


class Message:
    """
    Class, that implements messages in chat.
    """
    
    def __init__(
        self, 
        content: str, 
        *,
        role: str='user',
        user_id: str=None,
        chat_id: str=None,
        datetime_sent: datetime=None,
        is_reply: bool=False,
        reply: 'Message'=None,
        is_forward: bool=False,
        forward: List['Message']=None,
        media: List[BaseMedia]=None,
    ):
        """
        Initializes an instance of a class.
        Args:
            content: [str]: Message content.
            role: [str]: Role of message author in system. Can be 'user'/'assistant'/'system'
            user_id: [str]: Unique ID of user, who has sent this message.
            chat_id: [str]: Unique ID of a chat, where message has been sent.
            datetime_sent: [datetime.datetime]: Timestamp, where the message has been sent.
            is_reply: [bool]: Whether the message is a reply for another message from the same chat.
            reply: [Message]: If current message is a reply, then this argument is a previous message, which is replied.
            is_forward: [bool]: Whether the message is a forwarded sequence of messages from a chat.
            forward: [List[Message]]: Forwarded messages from a chat.
            media: List[BaseMedia]: List of mediafiles, attached to this message. 
        """
        # Here is a private part of the class.
        # Place every private attribute between '_lock's.
        # Each private element should start with one underscore.
        self._lock = False
        self._bot_data = ['role', 'content']
        self._lock = True
        # This is a public part of class.
        self.content = content
        self.role = role
        self.user_id = user_id
        self.chat_id = chat_id
        self.datetime_sent = datetime_sent
        self.status = []
        self.n_replies = 0
        self.is_reply = is_reply
        if self.is_reply:
            self.reply = reply
            self.reply.n_replies += 1
        else:
            self.reply = None
        self.is_forward = is_forward
        if self.is_forward:
            self.forward = forward
        else:
            self.forward = None
        self.reactions = []
        if media is None:
            self.media = []
        else:
            self.media = media
            
    def __delitem__(self, item: str):
        raise KeyError("Access denied.")
            
    def __setitem__(self, item: str, value: Any):
        self.__setattr__(item, value)
        
    def __getitem__(self, item: str):
        return self.__getattribute__(item)
        
    def __delattr__(self, attr: str):
        raise AttributeError("Access denied.")
            
    def __setattr__(self, attr: str, value: Any):
        if attr == 'restricted':
            raise AttributeError("Access denied.")
        if attr.startswith('__'):
            raise AttributeError("Access denied.")
        if attr == '_lock' and attr not in self.__dict__:
            super().__setattr__(attr, value)
            return
        if attr == '_lock' and attr in self.__dict__ and self._lock:
            raise AttributeError("Access denied.")
        if not self._lock:
            super().__setattr__(attr, value)
            return
        if self._lock and attr in self.restricted:
            raise AttributeError("Access denied.")
        else:
            super().__setattr__(attr, value)
            return
            
    def __getattribute__(self, attr: str):
        if attr.startswith('__'):
            return super().__getattribute__(attr)
        if attr == '_lock':
            return super().__getattribute__(attr)
        if attr == 'restricted':
            return super().__getattribute__(attr)
        if attr in self.restricted:
            raise AttributeError("Access denied.")
        return super().__getattribute__(attr)
    
    def __len__(self):
        return len(self.content)
    
    def __iter__(self):
        return self.content.__iter__()
    
    def __add__(self, other: Any) -> str:
        return self.content + other.__str__()
    
    def __radd_(self, other: Any) -> str:
        return self.__add__(other)
    
    def __iadd__(self, other: Any):
        self.content += other.__str__()
        return self
    
    def __mul__(self, other: Any) -> str:
        return self.content * other.__int__()
    
    def __rmul__(self, other: Any) -> str:
        return self.__mul__(other)
    
    def __imul__(self, other: Any):
        self.content *= other.__int__()
        return self
    
    def __eq__(self, other: Any) -> bool:
        if self.content == other.__str__():
            return True
        return False
    
    def __neq__(self, other: Any) -> bool:
        return not self.__eq__(other)
            
    def __repr__(self):
        return self.__dict__.__str__()
    
    def __str__(self):
        return self.content
    
    @staticmethod
    def is_restricted(attribute: str) -> bool:
        if len(attribute) > 1:
            if attribute[0] == '_' and attribute[1] != '_':
                return True
            return False
        if attribute[0] == '_':
            return True
        return False
    
    @property
    def restricted(self):
        return [attr for attr in self.__dict__.keys() if self.__class__.is_restricted(attr)]
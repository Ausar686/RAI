from typing import Union
from collections import deque

import tiktoken


class TokenCounter:
    _tokens_per_message = 3,
    
    def __init__(self, model: str="gpt-3.5-turbo"):
        self.model = model
        self.encoding = tiktoken.encoding_for_model(self.model)
        return
    
    def count(self, obj: Union[str, dict, list]) -> int:
        if isinstance(obj, str):
            return self.count_from_str(obj)
        elif isinstance(obj, dict):
            return self.count_from_dict(obj)
        elif isinstance(obj, list):
            return self.count_from_list(obj)
        elif isinstance(obj, deque):
            # Counting for list and deque are the same
            return self.count_from_list(obj)
        else:
            raise TypeError(f"Parameter 'obj' must be str, dict, list or deque, not {type(obj)}.")
            
    def count_from_str(self, string: str) -> int:
        return len(self.encoding.encode(string))
    
    def count_from_dict(self, dct: dict) -> int:
        # Here we assume, that a message is provided in OpenAI dict form:
        # {"role": role, "content": content}
        # So we simply call 'count_from_str' on content
        return self.count_from_str(dct.get("content"))
    
    def count_from_list(self, lst: list) -> int:
        # Here we assume that a list of messages in OpenAI dict form is given:
        # [{"role": role, "content": content}, ...]
        # So we simply iterate over the list and call 'count_from_dict'
        n_tokens = 0
        for message in lst:
            num_tokens += self._tokens_per_message
            num_tokens += self.count_from_dict(message)
        num_tokens += 3 # every reply is primed with <|start|>assistant<|message|>
        return num_tokens
from typing import Union
from collections import deque

from .token_counter import TokenCounter
from .qagpt import QAGPT


class TextSummarizer:
    
    # These constants can be edited
    # if they prove to be non-sufficient for output storage.
    _limits = {
        "gpt-3.5-turbo-16k": 15000,
        "gpt-4-32k": 30000
    }
    
    _upgrades = {
        "gpt-3.5-turbo": "gpt-3.5-turbo-16k",
        "gpt-4": "gpt-4-32k"
    }
    
    _max_words = 200
    
    def __init__(self, model: str="gpt-3.5-turbo", n_words: int=50):
        if n_words > self._max_words:
            raise ValueError("Too many words for summary. Maximum 200 words allowed.")
        self.model = model
        self.upgrade_model()
        self.n_words = n_words
        self.token_counter = TokenCounter(self.model)
        self.gpt = QAGPT(model=self.model)
        return
    
    def upgrade_model(self) -> None:
        # Upgrades model to the one with higher token cap
        # If it's not possible, does nothing
        try:
            self.model = self._upgrades[self.model]
            return
        except KeyError:
            pass
    
    @property
    def prompt(self):
        prompt = f"""
            <INSTRUCTION>
            Напиши краткое содержание текста ниже.
            В кратком содержании должно быть максимум {self.n_words} слов.
            Ответ выпиши на русском языке.
            """
        return prompt
    
    @staticmethod
    def dict2str(dct: dict) -> str:
        # Converts message in a dict form to message in a dialog (string) form
        return f"[{dct.get('role')}]: {dct.get('content')}"
        
    def summarize(self, obj: Union[str, list, dict]) -> str:
        # Raw text for summariztaion
        if isinstance(obj, str):
            return self.summarize_str(obj)
        # Message dict for summarization
        elif isinstance(obj, dict):
            return self.summarize_dict(obj)
        # List of messages for summarization
        elif isinstance(obj, list):
            return self.summarize_list(obj)
        elif isinstance(obj, deque):
            # If a deque is given, process it as a list.
            return self.summarize_list(obj)
        else:
            raise TypeError(f"Unsupported type {type(obj)} for argument 'obj'.",
                            f"Only str, dict and list are supported.")
        
    def summarize_str(self, string: str) -> str:
        request = self.prompt + f"""
            <TEXT>
            {string}
            """
        n_tokens = self.token_counter.count(request)
        # If text is super long, split it in 2 parts
        if n_tokens > self._limits[self.model]:
            lines = request.split("\n")
            n_lines = len(lines)
            batch = "\n".join(lines[:n_lines//2])
            n_tokens_batch = self.token_counter.count(batch)
            if n_tokens_batch > self._limits[self.model]:
                # Probably, it's a very long single message.
                # Summarize it in a bruteforce manner.
                return self.brute_summarize(string)
            summary = self.summarize_str(batch)
            new_string = summary + "\n" + "\n".join(lines[n_lines//2:])
            return self.summarize_str(new_string)
        answer = self.gpt.get_str(request)
        return answer
    
    def summarize_dict(self, dct: dict) -> str:
        # Convert message in a dict form to message in a dialog (string) form.
        # And then call 'summarize_str'
        string = self.dict2str(dct)
        return self.summarize_str(string)
    
    def summarize_list(self, lst: list) -> str:
        # Convert all messages from the list (dicts) to strings
        # Then join the strings via newline
        # And then call 'summarize_str'
        strings = [self.dict2str(dct) for dct in lst]
        string = "\n".join(strings)
        return self.summarize_str(string)
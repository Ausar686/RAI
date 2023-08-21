# Created by: Ausar686
# https://github.com/Ausar686

from typing import Any
from collections import defaultdict


class RDict(defaultdict):
    """
    RAI wrapper class for defaultdict, which implements attribute addressing
    in addition to item addressing.
    Example:
        dct = RDict(str)
        dct["a"] = 123
        print(dct.a)
        >>> 123
    Note:
        Do NOT use basic method names as the keys, because it will not work properly if
        you address to them via attribute.
        Example:
            dct = RDict(str)
            dct["keys"] = 1234
            print(dct.keys)
            >>> <function RDict.keys> # There exists a default dict method, called 'keys'
        To obtain basic attributes' and methods' names use this:
            print(dir(defaultdict()))
        Or:
            print(defaultdict().__dict__)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._internal_attribute_names_set = set(dir(self))
        return
    
    def __setattr__(self, attr: str, value: Any) -> None:
        """
        Override a __setattr__ method, so that it sets an item to the dictionary.
        """
        if attr == "_internal_attribute_names_set":
            super().__setattr__(attr, value)
            return
        if attr in self._internal_attribute_names_set:
            raise AttributeError(f"Can't assign value to attribute {attr}. Access denied.")
        self[attr] = value
        return
    
    def __getattr__(self, attr: str) -> Any:
        """
        This method is called whenever you request an attribute that does not exist.
        It returns an item from the dict with the same key, if such a key exists in a dict.
        Otherwise it raises AttributeError.
        """
        if attr in self.keys():
            return self.get(attr)
        else:
            raise AttributeError("Attribute does not exist.")
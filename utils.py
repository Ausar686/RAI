# Created by: Ausar686
# https://github.com/Ausar686

from typing import Any

import requests

from .containers.rdict import RDict


def method_logger(func):
    """
    Special decorator for logging RAI ChatBot methods.
    """
    
    def start_log(func_name, args, kwargs):
        strings = [
            f"[INFO]: EXECUTING: {func.__name__}",
            f"[INFO]: Args: {args}",
            f"[INFO]: Kwargs: {kwargs}"
        ]
        print("\n".join(strings))
        return
    
    def end_log(func_name, args, kwargs):
        strings = [
            f"[INFO]: FINISHED: {func.__name__}",
            f"[INFO]: Args: {args}",
            f"[INFO]: Kwargs: {kwargs}"
        ]
        print("\n".join(strings))
        return
        
    def safe_log(logger, obj, func_name, args, kwargs):
        try:
            if obj.log:
                logger(func_name, args, kwargs)
        except Exception:
            pass
        return
    
    def wrapper(*args, **kwargs):
        obj = args[0]
        safe_log(start_log, obj, func.__name__, args, kwargs)
        res = func(*args, **kwargs)
        safe_log(end_log, obj, func.__name__, args, kwargs)
        return res
    
    return wrapper


def retry(n_retries: int=5):
    """
    Retrying decorator function.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            n = n_retries
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    n -= 1
                    if n <= 0:
                        raise
        return wrapper
    return decorator


def to_rdict(obj: object, recursive: bool=True) -> RDict:
    """
    Converts JSON-like object into RDict.
    Args:
        obj[object]: JSON-like object to convert.
        recursive[bool]: Whether to convert all nested JSON-like objects. Default: True.
    Returns:
        RDict
    """
    if not (isinstance(obj, list) or isinstance(obj, dict)):
        return obj
    # Iterate over list elements, if convertion is recursive
    elif isinstance(obj, list):
        if not recursive:
            return obj
        return [to_rdict(elem) for elem in obj]
    # Iterate over dict elements, if convertion is recursive
    elif isinstance(obj, dict):
        if not recursive:
            return RDict(obj)
        return RDict({key: to_rdict(value) for key, value in obj.items()})

def request_openai(**kwargs) -> dict:
    """
    Sends request to OpenAI API endpoint in order to obtain response.
    Is mainly used for chat-like interactions with GPT API.
    """
    url = "https://api.openai.com/v1/chat/completions"
    api_key = kwargs.pop("api_key", None)
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.post(url, headers=headers, json=kwargs)
    return r.json()
from typing import Union

from .message import Message


def message_to_openai(message: Union[Message, str, dict]) -> dict:
    """
    Converts a given message to an OpenAI API input structure:
    Args:
        message: [Message|str|dict]: A message to convert
    Returns:
        openai_message: A dict of the following structure:
            {'role': role, 'content': content}
    """
    if isinstance(message, Message):
        return {'role': message.role, 'content': message.content}
    elif isinstance(message, str):
        return {'role': 'user', 'content': message}
    elif isinstance(message, dict):
        return {'role': message['role'], 'content': message['content']}
    else:
        raise TypeError("Invalid type to convert to OpenAI input message.\nSupported types are: str, dict, rai.Message.")
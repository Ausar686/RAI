from typing import Any, Union
import json
import os

import openai
from openai.openai_object import OpenAIObject

from .token_counter import TokenCounter
from .text_summarizer import TextSummarizer
from ..chat import  Chat, Message
from ..containers import RDict 
from ..profile import Profile
from ..utils import method_logger, retry


class ChatBot:
    """
    RAI class for chat-like interaction with OpenAI API using customizable set of actors.
    """
    
    _defaults = RDict(None, {
        "openai": RDict(None, {
            "api_key": None,
            "model": "gpt-3.5-turbo",
            "temperature": 0,
            "stream": False,
            "n": 1,
            "time_sleep": 2,
        }),
        "limits": RDict(None, {
            "gpt-3.5-turbo": 3500,
            "gpt-3.5-turbo-16k": 15500,
            "gpt-4": 7500,
            "gpt-4-32k": 31500
        }),
        "upgrades": RDict(None, {
            "gpt-3.5-turbo": "gpt-3.5-turbo-16k",
            "gpt-4": "gpt-4-32k"
        }),
        "downgrades": RDict(None, {
            "gpt-3.5-turbo-16k": "gpt-3.5-turbo",
            "gpt-4-32k": "gpt-4"
        }),
        "chat": RDict(None, {
            "username": "DefaultUser",
            "bot_name": "DefaultBot"
        }),
        "text_summarizer": RDict(None, {
            "model": "gpt-3.5-turbo",
            "n_words": 50
        }),
        "token_counter": RDict(None, {
            "model": "gpt-3.5-turbo"
        }),
        "qagpt": RDict(None, {
            "model": "gpt-3.5-turbo",
            "temperature": 0,
            "stream": False,
            "n": 1
        })
    })
    
    # Errors initialization
    _api_key_error = """
        OpenAI API key must be provided in one of two ways.
        1. Via .json configuration file:
            "openai": {
                "api_key": "YOUR_KEY_HERE",
                ...
            }
        2. Via environment variable "OPENAI_API_KEY".
    """
    
    _last_message_len_error = "Last message is too long to proceed."
    
    _n_answers_error = "Several answers option is not implemented yet."
    
    _mode_error = "Wrong mode. Available modes are: 'console' and 'app'"
        
    def __init__(
        self,
        config_path: str,
        actors_config_path: str=None,
        mode: str="console",
        *,
        profile: Profile=None,
        log: bool=False) -> None:
        """
        Initializes ChatBot instance using 2 config files.
        """
        # Initialize utils for uploading data from '.ini' config file
        self.log = log
        self.name = None
        self.config_dir = None
        self.parameters = RDict()
        self.actors = RDict()
        self._synced_actors = []
        self._runtime_mode = mode
        # Load config options from '.json' config file
        self.from_config(config_path)
        # Set OpenAI API key
        self.set_openai_parameters()
        # Setup actors from config
        self.actors_from_config(actors_config_path)
        # Initialize dialog attributes
        self.init_messages(profile)
        # Validate initialization
        self.validate_init()
        return
    
    @method_logger
    def from_config(self, config_path: str=None) -> None:
        """
        Runs instance initialization from .json configuration file.
        """
        if config_path is None:
            return
        if self.config_dir is None:
            self.config_path = os.path.split(os.path.abspath(config_path))[0]
        with open(config_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        for section in data.keys():
            section_data = data.get(section)
            self.process_section(section, section_data)
        return
    
    @method_logger
    def process_section(self, section: str, section_data: Union[dict, str]) -> None:
        """
        Processes one section of the configuration file.
        """
        # Initialize from parent config file.
        if section == "root":
            self.from_config(section_data)
            return
        # Set bot name
        elif section == "name":
            self.name = section_data
            return
        # Set attribute as a key in self.parameters dict
        # if it's not present yet
        if not hasattr(self, section):
            self.parameters[section] = RDict(str)
        for option, value in section_data.items():
            self.process_option(section, option, value)
        return
    
    @method_logger
    def process_option(self, section: str, option: str, value: Any=None) -> None:
        """
        Processes one option in a section of the configuration file.
        """
        self.parameters[section][option] = value
        return
    
    @method_logger
    def actors_from_config(self, actors_config_path: str=None) -> None:
        """
        Initializes ChatBot actors from .json configuration file.
        """
        if actors_config_path is None:
            self.set_default_actors()
            return
        with open(actors_config_path, "r", encoding="utf-8") as json_file:
            actors_json = json.load(json_file)
        for actor in actors_json:
            name = actor.get("name")
            class_name = actor.get("class")
            kwargs = actor.get("params")
            sync = actor.get("sync_models")
            exec(f"from RAI import {class_name}")
            exec(f"self.actors[{name}] = {class_name}(**{kwargs})")
            if sync:
                self._synced_actors.append(self.actors[name])
        return
    
    @method_logger
    def set_default_actors(self):
        """
        Initializes default ChatBot actors.
        """
        self.actors.token_counter = TokenCounter(self.openai.model)
        self.actors.summarizer = TextSummarizer(self.actors.token_counter.model, self._defaults.text_summarizer.n_words)
        self._synced_actors.append(self.actors.token_counter)
        return
    
    @method_logger
    def set_api_key(self) -> None:
        """
        Sets OpenAI API key.
        """
        if not hasattr(self.openai, "api_key") or self.openai.api_key is None:
            self.openai.api_key = os.getenv("OPENAI_API_KEY")
        if self.openai.api_key is None:
            raise ValueError(self._api_key_error)
        openai.api_key = self.openai.api_key
        return
    
    @method_logger
    def set_openai_parameters(self) -> None:
        """
        Sets all required OpenAI API parameters (including API key).
        """
        if not hasattr(self, "openai"):
            raise ValueError("OpenAI section is not present in configuration files.")
        for key, value in self._defaults.openai.items():
            if key == "api_key":
                self.set_api_key()
                return
            if key not in self.openai:
                self.openai[key] = value
        return
    
    @method_logger
    def set_instruction(self) -> None:
        """
        Sets bot instruction in a string representation as an attribute.
        """
        self.instruction = "<INSTRUCTIONS>\n" + "\n".join([f"{key}: {value}" for key, value in self.instructions.items()])
        return
    
    @method_logger
    def set_system_message(self) -> None:
        """
        Sets system message in OpenAI notation for the bot as an attribute.
        """
        self.set_instruction()
        self.system_message = Message({"role": "system", "content": self.instruction, "username": "ROOT"})
        return
    
    @method_logger
    def init_messages(self, profile: Profile) -> None:
        """
        Initializes dialog attributes.
        'chat' is an internal message storage (will NOT be sent to API).
        'context' is a list of messages in OpenAI notation (will be sent to API).
        """
        if profile is None:
            self.username = self._defaults["chat"]["username"]
        else:
            self.username = profile.user_data.username
        if self.name is None:
            self.name = self._defaults["chat"]["bot_name"]
        self.set_system_message()
        chat_dct = {"username": self.username, "bot_name": self.name, "messages": [self.system_message]}
        self.chat = Chat(chat_dct)
        self.context = [self.system_message.to_openai()]
        return
    
    @method_logger
    def validate_init(self) -> None:
        """
        Validates initialization. Use this method to raise exceptions for not implemented options.
        """
        if self.openai.n > 1:
            raise NotImplementedError(self._n_answers_error)
        if self._runtime_mode not in ["console", "app"]:
            raise NotmplementedError(self._mode_error)

    @property
    def messages(self) -> list:
        """
        Returns all messages in self.chat
        """
        return self.chat.messages
    
    @property
    def last_message(self) -> Message:
        """
        Returns last message in self.chat or None if self.chats is empty.
        """
        return self.chat.last if self.chat else None
    
    def append(self, msg: Message) -> None:
        """
        Appends message both to context and to chat.
        """
        self.chat.append(msg)
        self.context.append(msg.to_openai())
        return
    
    def user_message(self, text: str) -> Message:
        """
        Converts text to Message with user data.
        """
        msg_dct = {"role": "user", "content": text, "username": self.username}
        msg = Message(msg_dct)
        return msg
    
    def bot_message(self, text: str) -> Message:
        """
        Converts text to Message with bot data.
        """
        msg_dct = {"role": "assistant", "content": text, "username": self.name}
        msg = Message(msg_dct)
        return msg
    
    def sys_message(self, text: str) -> Message:
        """
        Converts text to message with system data.
        """
        msg_dct = {"role": "system", "content": text, "username": "ROOT"}
        msg = Message(msg_dct)
        return msg
    
    def add_user_message(self, text: str) -> None:
        """
        Appends user message both to context and to chat.
        """
        msg = self.user_message(text)
        self.append(msg)
        return
    
    def add_bot_message(self, text: str) -> None:
        """
        Appends bot message both to context and to chat.
        """
        msg = self.bot_message(text)
        self.append(msg)
        return
    
    def upgrade_model(self) -> None:
        """
        Upgrades token limit of the using OpenAI API model.
        """
        self.openai.model = self._defaults.upgrades[self.openai.model]
        self.set_actors_model()
        return
    
    def downgrade_model(self) -> None:
        """
        Downgrades token limit of the using OpenAI API model.
        """
        self.openai.model = self._defaults.downgrades[self.openai.model]
        self.set_actors_model()
        return
    
    def set_actors_model(self) -> None:
        """
        Syncronizes models among all required actors in instance.
        """
        for actor in self._synced_actors:
            actor.set_model(self.openai.model)
        return
    
    def verify_context(self) -> None:
        """
        Verifies, that context length is not out-of-range.
        If it is, summarizes the context and updates it.
        Updated context contains system message, summary and last message.
        Chat data is not affected by this method.
        """
        if self.actors.token_counter.run(self.context) > self._defaults.limits[self.openai.model]:
            # Check for huge prompt injection
            if self.actors.token_counter.run(self.last_message) > self._defaults.limits[self.openai.model]:
                try:
                    self.upgrade_model()
                except KeyError:
                    self.fix_injection()
                self.verify_context()
                return
            summary = self.actors.summarizer.run(self.context[1:-1])
            msg = self.sys_message(summary)
            msg_list = [self.system_message, msg, self.last_message]
            self.context = [elem.to_openai() for elem in msg_list]
            try:
                self.downgrade_model()
            except KeyError:
                pass
            return
        return
    
    def fix_injection(self) -> None:
        """
        Fixes huge message injection by popping it from context.
        Also writes an error log message.
        """
        error_text = self._last_message_len_error
        error_msg = self.bot_message(error_text)
        self.chat.append(error_msg)
        self.context.pop()
        return
    
    @retry(5)
    def get_completion(self) -> OpenAIObject:
        """
        Sends context to OpenAI API and receives response from it as a completion.
        """
        completion = openai.ChatCompletion.create(
            messages=self.context,
            model=self.openai.model,
            temperature=self.openai.temperature,
            stream=self.openai.stream,
            n=self.openai.n
        )
        return completion
    
    @retry(5)
    async def aget_completion(self) -> OpenAIObject:
        """
        Sends context to OpenAI API and receives response from it as a completion.
        """
        completion = await openai.ChatCompletion.acreate(
            messages=self.context,
            model=self.openai.model,
            temperature=self.openai.temperature,
            stream=self.openai.stream,
            n=self.openai.n
        )
        return completion
    
    @staticmethod
    def completion_to_openai_message_list(completion: OpenAIObject) -> list:
        lst = [choice.message for choice in completion.choices]
        return lst
    
    @staticmethod
    def openai_message_list_to_dict(lst: list) -> dict:
        """
        Converts list of messages
        """
        # [TODO]: Add proper processing of several generated variants
        return lst[0]
    
    def get_answer(self) -> Message:
        """
        Full pipeline of answer obtaining from OpenAI API.
        """
        completion = self.get_completion()
        message_list = self.completion_to_openai_message_list(completion)
        msg_dct = self.openai_message_list_to_dict(message_list)
        msg = Message(msg_dct)
        return msg
    
    async def aget_answer(self) -> Message:
        """
        Full pipeline of answer obtaining from OpenAI API.
        """
        completion = await self.aget_completion()
        message_list = self.completion_to_openai_message_list(completion)
        msg_dct = self.openai_message_list_to_dict(message_list)
        msg = Message(msg_dct)
        return msg
    
    def display(self) -> None:
        """
        Displays last message as a formatted string.
        """
        print(f"[{self.last_message.username}]: {self.last_message.content}")
        return
    
    def input(self) -> None:
        """
        User input option for console mode.
        """
        if self._runtime_mode == "app":
            return
        content = input(f"[{self.username}]: ")
        msg = self.user_message(content)
        return msg
    
    def process_input(self) -> None:
        """
        User input processing method for both app and console modes.
        """
        if self._runtime_mode == "app":
            return
        msg = self.input()
        self.append(msg)
        return
    
    def run(self) -> None:
        """
        Main method. Executes dialogue with chat-bot.
        Currently only console mode is implemented.
        """
        if self._runtime_mode == "app":
            return
        while not self.is_over:
            msg = self.get_answer()
            self.append(msg)
            self.display()
            self.process_input()
            self.verify_context()
        return
        
    @property    
    def is_over(self) -> bool:
        """
        A property, that represents, whether the dialogue is ended by user.
        """
        return not bool(self.last_message.content)
    
    def __getattr__(self, attr: str) -> Any:
        """
        Provides attribute access to self.parameters
        Note: Do not use default names as parameters attributes, as it will not work properly with __getattr__
        """
        if attr in self.parameters:
            return self.parameters.get(attr)
        raise AttributeError(f"Attribute {attr} does not exist.")
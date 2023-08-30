# Created by: Ausar686
# https://github.com/Ausar686

from typing import Any, Union
import hashlib
import json
import os
import re

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
    
    _runtime_modes_available = ["console", "app"]
    
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
    
    _mode_error = f"Wrong mode value. Available modes are: {_runtime_modes_available}"
        
    def __init__(
        self,
        config_path: str,
        actors_config_path: str=None,
        functions_config_path: str=None,
        *,
        mode: str="console",
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
        # Set OpenAI API parameters
        self.set_openai_parameters()
        # Setup actors from config
        self.actors_from_config(actors_config_path)
        # Setup usable functions from config.
        self.functions_from_config(functions_config_path)
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
            # Set only default actors
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
        # Set default actors if they are not set yet.
        self.set_default_actors()
        return
    
    @method_logger
    def set_default_actors(self):
        """
        Initializes default ChatBot actors.
        """
        if "token_counter" not in self.actors:
            self.actors.token_counter = TokenCounter(self.openai.model)
        if "summarizer" not in self.actors:
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
        # Set environmental variable to prevent overriding by further imports
        os.environ["OPENAI_API_KEY"] = self.openai.api_key
        return
    
    @method_logger
    def set_openai_parameters(self) -> None:
        """
        Sets all required OpenAI API parameters (excluding API key).
        """
        if not hasattr(self, "openai"):
            raise ValueError("OpenAI section is not present in configuration files.")
        for key, value in self._defaults.openai.items():
            if key == "api_key":
                self.set_api_key()
                continue
            if key not in self.openai:
                self.openai[key] = value
        return
    
    @method_logger
    def functions_from_config(self, functions_config_path: str=None) -> None:
        """
        Set functions list in JSON notation to use in OpenAI API calls.
        """
        if functions_config_path is None:
            self.set_default_functions()
            return
        with open(functions_config_path, "r", encoding="utf-8") as json_file:
            self.usable_functions = json.load(json_file)
        self._usable_functions_names = [elem["name"] for elem in self.usable_functions]
        return
    
    @method_logger
    def set_default_functions(self) -> None:
        """
        Set default list of functions (None) to use in OpenAI API calls.
        """
        self.usable_functions = None
        self._usable_functions_names = None
        return
    
    @method_logger
    def set_instruction(self) -> None:
        """
        Sets bot instruction in a string representation as an attribute.
        """
        self.instruction = "###INSTRUCTIONS###\n" + "\n\n".join([f"<{key}>: {value}" for key, value in self.instructions.items()])
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
        self.profile = profile
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
    
    def bot_message(self, text: Any) -> Message:
        """
        Converts text to Message with bot data.
        """
        msg_dct = {"role": "assistant", "content": str(text), "username": self.name}
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

    def __len__(self) -> int:
        """
        Returns the current size of the bot context in tokens.
        """
        return self.actors.token_counter.run(self.context)

    @property
    def last_message_len(self) -> int:
        """
        Returns the current size of the last message in tokens
        """
        return self.actors.token_counter.run(self.last_message)

    @property
    def size_limit(self) -> int:
        """
        Returns available token size limit for context for self.openai.model
        """
        return self._defaults.limits[self.openai.model]
    
    def verify_context(self) -> None:
        """
        Verifies, that context length is not out-of-range.
        If it is, summarizes the context and updates it.
        Updated context contains system message, summary and last message.
        Chat data is not affected by this method.
        """
        if len(self) > self.size_limit:
            # Check for huge prompt injection
            if self.last_message_len > self.size_limit:
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
        (ASYNC) Sends context to OpenAI API and receives response from it as a completion.
        """
        completion = await openai.ChatCompletion.acreate(
            messages=self.context,
            model=self.openai.model,
            temperature=self.openai.temperature,
            stream=self.openai.stream,
            n=self.openai.n
        )
        return completion
    
    @retry(5)
    def fget_completion(self) -> OpenAIObject:
        """
        Sends context to OpenAI API and receives response from it as a completion.
        Response CAN contain a function call from self.usable_functions.
        """
        if self.usable_functions is None:
            return self.get_completion()
        completion = openai.ChatCompletion.create(
            messages=self.context,
            model=self.openai.model,
            temperature=self.openai.temperature,
            stream=self.openai.stream,
            n=self.openai.n,
            functions=self.usable_functions
        )
        return completion
    
    @retry(5)
    async def afget_completion(self) -> OpenAIObject:
        """
        (ASYNC) Sends context to OpenAI API and receives response from it as a completion.
        Response CAN contain a function call from self.usable_functions.
        """
        if self.usable_functions is None:
            return await self.aget_completion()
        completion = await openai.ChatCompletion.acreate(
            messages=self.context,
            model=self.openai.model,
            temperature=self.openai.temperature,
            stream=self.openai.stream,
            n=self.openai.n,
            functions=self.usable_functions
        )
        return completion
    
    @staticmethod
    def completion_to_openai_message_list(completion: OpenAIObject) -> list:
        """
        Converts OpenAI Completion (OpenAIObject) to a list of choices.
        """
        lst = [choice.message for choice in completion.choices]
        return lst
    
    @staticmethod
    def openai_message_list_to_dict(lst: list) -> OpenAIObject:
        """
        Converts list of messages to an OpenAIObject:
        {"role": role, "content": content}
        """
        # [TODO]: Add proper processing of several generated variants
        return lst[0]

    @staticmethod
    def remove_numeration(text: str) -> str:
        """
        Removes numeration from the text, thus converting numerated lists into plain text.
        """
        re_text = re.sub(r"(\n+?)\d+\.\s*(.*?)(\n+?)", r"\n\2", text)
        return re_text
    
    def call_from_completion(self, completion: OpenAIObject) -> Any:
        """
        Calls function from OpenAI Completion.
        Raises ValueError if function is not presented in self.usable_functions
        """
        # [TODO]: Add processing of multiple choices.
        message = completion.choices[0].message
        call_data = message.function_call
        func_name = call_data.name
        if func_name not in self._usable_functions_names:
            raise ValueError(f"Function {func_name} is not available to call.")
        arg_string = call_data.arguments
        kwargs = json.loads(arg_string)
        content = eval(f"self.{func_name}(**{kwargs})")
        msg = self.bot_message(content)
        return msg
    
    async def acall_from_completion(self, completion: OpenAIObject) -> Any:
        """
        (ASYNC) Calls function from OpenAI Completion.
        Raises ValueError if function is not presented in self.usable_functions
        """
        # [TODO]: Add processing of multiple choices.
        message = completion.choices[0].message
        call_data = message.function_call
        func_name = call_data.name
        if func_name not in self._usable_functions_names:
            raise ValueError(f"Function {func_name} is not available to call.")
        arg_string = call_data.arguments
        kwargs = json.loads(arg_string)
        content = eval(f"await self.{func_name}(**{kwargs})")
        msg = self.bot_message(content)
        return msg
    
    def completion_to_message(self, completion: OpenAIObject) -> Message:
        """
        Converts OpenAI Completion into a Message
        """
        msg_lst = self.completion_to_openai_message_list(completion)
        msg_dct = self.openai_message_list_to_dict(msg_lst)
        msg_dct["content"] = self.remove_numeration(msg_dct["content"])
        msg = Message(msg_dct)
        return msg
    
    def process_completion(self, completion: OpenAIObject) -> Any:
        """
        Processes the completion.
        If function call is required, calls it and returns the result.
        """
        # [TODO]: Add processing of multiple choices.
        finish_reason = completion.choices[0].finish_reason
        if finish_reason == "stop":
            return self.completion_to_message(completion)
        elif finish_reason == "function_call":
            return self.call_from_completion(completion)
        else:
            raise ValueError(f"Invalid value of 'finish_reason': {finish_reason}")
            
    async def aprocess_completion(self, completion: OpenAIObject) -> Any:
        """
        (ASYNC) Processes the completion.
        If function call is required, calls it and returns the result.
        """
        # [TODO]: Add processing of multiple choices.
        finish_reason = completion.choices[0].finish_reason
        if finish_reason == "stop":
            return self.completion_to_message(completion)
        elif finish_reason == "function_call":
            return await self.acall_from_completion(completion)
        else:
            raise ValueError(f"Invalid value of 'finish_reason': {finish_reason}")
    
    def get_answer(self) -> Message:
        """
        Full pipeline of answer obtaining from OpenAI API.
        """
        completion = self.get_completion()
        msg = self.process_completion(completion) 
        return msg
    
    async def aget_answer(self) -> Message:
        """
        (ASYNC) Full pipeline of answer obtaining from OpenAI API.
        """
        completion = await self.aget_completion()
        msg = await self.aprocess_completion(completion) 
        return msg

    def fget_answer(self) -> Message:
        """
        Full pipeline of answer obtaining from OpenAI API.
        """
        # [TODO]: Add proper exception handling
        try:
            completion = self.fget_completion()
            msg = self.process_completion(completion)
            return msg
        except Exception:
            return self.get_answer()
    
    async def afget_answer(self) -> Message:
        """
        (ASYNC) Full pipeline of answer obtaining from OpenAI API.
        """
        # [TODO]: Add proper exception handling
        try:
            completion = await self.afget_completion()
            msg = await self.aprocess_completion(completion) 
            return msg
        except Exception:
            return await self.aget_answer()

    @property
    def last_message_fstring(self) -> str:
        """
        Returns last message as a formatted string.
        """
        return f"[{self.last_message.username}]: {self.last_message.content}"

    @property    
    def is_over(self) -> bool:
        """
        A property, that represents, whether the dialogue is ended by user.
        """
        return not bool(self.last_message.content)

    def to_txt(self, path: str) -> None:
        """
        Writes chat in .txt file in the format below.
        Example:
            [Bot]: How can I assist you?
            [User]: I want to become rich.
            [Bot]: ...
            ..........
        """
        msg_lst =  [f"{msg.username}: {msg.content}" for msg in self.messages[1:]]
        text = "\n".join(msg_lst)
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return

    def clear(self) -> None:
        """
        Cleans the context for bot reusing
        NOTE: This method does NOT clean the entire chat (self.chat)
        """
        self.context.clear()
        self.context.append(self.system_message.to_openai())
        return
    
    def __getattr__(self, attr: str) -> Any:
        """
        Provides attribute access to self.parameters
        Note: Do not use default names as parameters attributes, as it will not work properly with __getattr__
        """
        if attr in self.parameters:
            return self.parameters.get(attr)
        raise AttributeError(f"Attribute {attr} does not exist.")

    # Here are some beta-feature methods, which will be useful in future updates.

    def hash_button_option(self, option: str) -> str:
        prefix = f"{self.username}~~~{self.name}"
        hashed_prefix = hashlib.sha256(str.encode(prefix)).hexdigest
        hashed_string = f"{hashed_prefix}\n{option}"
        return hashed_string

    # Here are some methods that can be usefully overridden in subclasses.
    # It is strongly recommended not to override the methods above this line (excluding __init__)
    
    def display(self, *args, **kwargs) -> None:
        """
        Displays last message as a formatted string.
        """
        print(self.last_message_fstring)
        return

    def process_output(self, *args, **kwargs) -> None:
        """
        Full pipeline of OpenAI output processing.
        """
        msg = self.get_answer()
        self.append(msg)
        self.display(*args, **kwargs) 
        return

    def fprocess_output(self, *args, **kwargs) -> None:
        """
        Full pipeline of OpenAI output processing.
        """
        msg = self.fget_answer()
        self.append(msg)
        self.display(*args, **kwargs) 
        return
    
    def input(self, *args, **kwargs) -> Message:
        """
        User input option for console mode.
        """
        if self._runtime_mode == "app":
            return
        content = input(f"[{self.username}]: ")
        msg = self.user_message(content)
        return msg
    
    def process_input(self, *args, **kwargs) -> None:
        """
        User input processing method for both app and console modes.
        """
        if self._runtime_mode == "app":
            return
        elif self._runtime_mode == "console":
            msg = self.input(*args, **kwargs)
            self.append(msg)
            return
        else:
            raise ValueError(self._mode_error)

    def fprocess_input(self, *args, **kwargs) -> None:
        """
        An alias for 'process_input' method to run with functions.
        """
        return self.process_input(*args, **kwargs)
    
    def run(self, *args, **kwargs) -> None:
        """
        Main method. Executes dialogue with chat-bot.
        Currently only console mode is implemented.
        """
        if self.usable_functions is not None:
            return self.frun(*args, **kwargs)
        if self._runtime_mode == "app":
            return self.run_in_app_mode(*args, **kwargs)
        elif self._runtime_mode == "console":
            return self.run_in_console_mode(*args, **kwargs)
        else:
            raise ValueError(self._mode_error)
            
    def frun(self, *args, **kwargs):
        """
        Main method. Executes dialogue with chat-bot.
        Currently only console mode is implemented.
        Function calls are enabled in this method 
        (instead of 'run', in which they are disabled)
        """
        if self._runtime_mode == "app":
            return self.frun_in_app_mode(*args, **kwargs)
        elif self._runtime_mode == "console":
            return self.frun_in_console_mode(*args, **kwargs)
        else:
            raise ValueError(self._mode_error)
    
    def run_in_app_mode(self, *args, **kwargs) -> None:
        """
        Runs bot in mobile application mode.
        """
        pass
    
    def run_in_console_mode(self, *args, **kwargs) -> None:
        """
        Runs bot in console mode.
        """
        while not self.is_over:
            self.process_output(*args, **kwargs)
            self.process_input(*args, **kwargs)
            self.verify_context()
        else:
            self.end_conversation(*args, **kwargs)
        return
    
    def frun_in_app_mode(self, *args, **kwargs) -> None:
        """
        Runs bot in mobile application mode.
        """
        pass
    
    def frun_in_console_mode(self, *args, **kwargs) -> None:
        """
        Runs bot in console mode.
        """
        while not self.is_over:
            self.fprocess_output(*args, **kwargs)
            self.fprocess_input(*args, **kwargs)
            self.verify_context()
        else:
            self.end_conversation(*args, **kwargs)
        return

    def end_conversation(self, *args, **kwargs) -> None:
        content = "Был рад помочь!"
        msg = self.bot_message(content)
        self.append(msg)
        self.display(*args, **kwargs)
        self.verify_context()
        self.chat.to_disk()
        return
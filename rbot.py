import os
import configparser

import openai


__version__ = '0.0.0'


class RBot:
    _openai_default_params = {
        "model": "gpt-3.5-turbo",
        "temperature": 0,
        "stream": False,
        "n": 1,
        "_time_sleep": 2,
    }
    
    def __init__(self, config_path: str, log: bool=False) -> None:
        self.log = log
        self.prompts = {}
        self.config_options = {}
        self._from_config(config_path)
        self._set_api_key()
        for param, value in self.__class__._openai_default_params.items():
            if param not in self.config_options:
                self.config_options[param] = value
            self.__setattr__(param, self.config_options[param])
        self.messages = [self._sys_message]
        self._all_messages = [self._sys_message]
        self.last_message = self._sys_message
        
    def _set_api_key(self) -> None:
        if not ("api_key" in self.config_options and self.config_options["api_key"]):
            try:
                self.config_options["api_key"] = os.getenv("OPENAI_API_KEY")
            except Exception:
                raise ValueError("""
                    OpenAI API key must be provided in one of two ways.
                    1. Via configuration file:
                    [config]
                    api_key = YOUR_KEY_HERE
                    2. Via environment variable 'OPENAI_API_KEY'.
                    """)
        openai.api_key = self.config_options["api_key"]
        return
        
    def _from_config(self, config_path: str) -> None:
        self.print(f"[INFO]: Successfully opened config file: {config_path}")
        filename = config_path.split(os.sep)[-1]
        directory = os.sep.join(config_path.split(os.sep)[:-1])
        config = configparser.ConfigParser()
        config.read(config_path)
        for section in config.sections():
            self.print(f"[INFO]: Started procceding SECTION '{section}' FROM FILE '{filename}'")
            if section != "config" and section not in self.prompts:
                self.prompts[section] = {}
            for option in config.options(section):
                self.print(f"[INFO]: Started proceeding OPTION: '{option}'")
                value = config.get(section, option)
                if not value:
                    continue
                if section == "config":
                    if option != "parent" and option not in self.config_options:
                        self.config_options[option] = ''
                    if option == "parent":
                        if value != 'ROOT':
                            parent_config_path = os.path.join(directory, value)
                            if self.log:
                                print(f"[INFO]: Calling parent config at: {parent_config_path}")
                            self._from_config(parent_config_path)
                            continue
                    elif option.startswith("n_"):
                        self.config_options[option] = float(value)
                    else:
                        self.config_options[option] = value
                else:
                    if option not in self.prompts[section]:
                        self.prompts[section][option] = ''
                    self.prompts[section][option] = value +'\n'
                self.print(f"[INFO]: Successfully procceeded option '{option}' from section '{section}' of file '{filename}'.")
        self.print(f"[INFO]: Successfully initialized bot from config.")
        return
    
    @property
    def instructions(self) -> str:
        instructions = self.prompts["instructions"]
        inst_str = instructions.get('wrapper') + ''.join([value for key, value in instructions.items() if key != 'wrapper'])
        return inst_str
    
    @staticmethod
    def _make_message(content: str, role: str='user') -> dict:
        return {'role': role, 'content': content}
    
    @property
    def _sys_message(self) -> str:
        return self.__class__._make_message(self.instructions, 'system')
    
    def _ask(self):
        while True:
            try:
                completion = openai.ChatCompletion.create(
                    messages=self.messages,
                    model=self.model,
                    temperature=self.temperature,
                    stream=self.stream,
                    n=self.n,
                )
                return completion
            except Exception as e:
                print(f"""
                [ERROR]: An exception has occured. Waiting {self._time_sleep} seconds to continue.
                Error: {e}""")
    
    @staticmethod
    def _completion_to_message(completion) -> dict:
        message = completion.choices[0].message
        return message
    
    def _get_answer(self) -> dict:
        completion = self._ask()
        message = self.__class__._completion_to_message(completion)
        return message
    
    def push(self, message: dict) -> None:
        self._all_messages.append(message)
        self.messages.append(message) # Update this later to stor finite amount of tokens in the conversation
        self.last_message = message
        return
    
    def update(self) -> None:
        message = self._get_answer()
        self.push(message)
        return
    
    def display(self) -> None:
        role = self.last_message["role"]
        content = self.last_message["content"]
        tag = "[RBot]" if role == 'assistant' else "[User]"
        print(f"{tag}: {content}")
        return
    
    def input(self) -> None:
        content = input("[User]: ")
        message = self.__class__._make_message(content)
        self.push(message)
        return

    def print(self, *args, **kwargs) -> None:
        if self.log:
            print(*args, **kwargs)
        return
        
    @property    
    def is_over(self) -> bool:
        return bool(self.last_message["content"])
    
    def run(self) -> None:
        while True:
            self.update()
            self.display()
            self.input()
            if self.is_over:
                break

    def execute(self, instruction: str):
        message = self._make_message(instruction)
        messages = [message]
        completion = openai.ChatCompletion.create(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            stream=False,
            n=1,
        )
        content = self._completion_to_message(completion).content
        return content
                    
    def __repr__(self) -> str:
        try:
            return self.config_options["repr"]
        except Exception:
            return f"Hello! I'm an RBot v{__version__}"
    
    def __str__(self) -> str:
        return self.__repr__()
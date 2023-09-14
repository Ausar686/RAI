# Created by: Ausar686
# https://github.com/Ausar686

from typing import Union
import os
import re
import time

from .base_actor import BaseActor
from ..containers.rdict import RDict
from ..utils import request_openai, to_rdict


class QAGPT(BaseActor):
    """
    Wrapping class around OpenAI API to simplify development and automatic usage.
    """
    # TODO: Test and improve wrapping prompts.
    # TODO: Implement streaming output.
    # TODO: Implement processing of different 'n' values.
    # TODO: Check implementation of methods, so that to use static/class methods where needed. 
    def __init__(
        self, 
        model: str='gpt-3.5-turbo', 
        key: str=None,
        temperature: float=0,
        stream: bool=False,
        n: int=1,
        ):
        """
        Initializes QAGPT(Qusetion-Answer GPT) object instance.
        Args:
            model (str): Type of model for API to use. Default: 'gpt-3.5-turbo'
            key (str): OpenAI API key. By default it's supposed, that you store it inside of 'OPENAI_API_KEY' environment variable. Default: None.
            temperature (float): Randomness of the results. The higher the value is, the more creative answers you will get.
                                 Lower values, yet, provide conservative answers. Should be in interval [0,2]. Default: 0.
            stream (bool): Whether to provide a omplete answer at once (False), or token-by-token (True). Default: False.
            n (int): Number of answers to generate. NOTE: Each answer consumes tokens. Default: 1. 
        """
        super().__init__(model)
        if stream:
            raise NotImplementedError("Streaming option coming soon...")
        if n > 1:
            raise NotImplementedError("Multiple output coming soon...")
        # Init OpenAI parameters
        self.openai = RDict()
        self.set_api_key(key)
        self.openai.model = self.model
        self.openai.temperature = temperature
        self.openai.stream = stream
        self.openai.n = n
        self._info = f"Instance of wrapping class around OpenAI API to simplify development and automatic usage.\nModel version: {self.model}"
        self._sleep_time = 2
        self._supported_types = ['int', 'float', 'list', 'dict', 'str']
        self._n_supported_types = len(self._supported_types)
        self._supported_roles = ['user', 'system', 'assistant']
        self._wrap_int_string = "Write only the integer as the answer."
        self._wrap_float_string = "Write only the float as the answer."
        self._wrap_prob_string = "Write only the float from interval [0, 1] as the answer. The closer the result is to 0, the less the probability is. The closer the result is to 1, the greater the probability is."
        self._wrap_dict_string = "Write the answer in Python dictionary notation. Write only the pairs key:value from the dictionary, separated by newline symbol."
        self._wrap_list_string = "Write only the list. Each element of the list should be written on a separate line."
        
    def set_api_key(self, key: str) -> None:
        """
        Method, that sets openai.api_key value.
        The API key is set only if it was None before calling the method. 
        Args:
            key (str): Value, that should be set as openai.api_key. If key is None gets an environmental variable 'OPENAI_API_KEY'
        Returns:
            None
        """
        if key is None:
            key = os.getenv("OPENAI_API_KEY")
        self.openai.api_key = key
        return

    def set_model(self, model: str) -> None:
        """
        Override for a base class method in order to remain compatible 
        with new format of RDict 'openai' as an attribute
        """
        super().set_model(model)
        if hasattr(self, "openai"):
            self.openai.model = model
        return
        
    def form_message(self, request: str, role: str="user") -> dict:
        """
        Takes text request and a given role in GPT-API and transforms it into a dictionary.
        Args:
            request (str): Text request to OpenAI API.
            role (str): String, which represents the role. Should be in ['user', 'system', 'assistant'].
                For further info about roles check GPT API documentation or community guides
                like this: https://vc.ru/u/1389654-machine-learning/625306-prostoe-rukovodstvo-po-chatgpt-api-s-ispolzovaniem-python
        Returns:
            message (dict): A dictionary for further processing with GPT-API.
        """
        assert role in self._supported_roles
        return {"role":role, "content":request}
    
    def form_messages(self, request: str, role: str="user") -> list:
        """
        Forms and returns a list from message, made with 'form_message' method.
        Args:
            request (str): Text request to OpenAI API.
            role (str): String, which represents the role. Should be in ['user', 'system', 'assistant'].
                For further info about roles check OpenAI API documentation: https://platform.openai.com/docs/api-reference/chat/create
        Returns:
            messages (list): List with dictionary (messages) made with 'form_message' method.
        """
        return [self.form_message(request, role)]
    
    def ask(self, messages: list) -> str:
        """
        Sends request to OpenAI server and returns a answer in string format.
        Args:
            messages (list): List of messages (dicts). By default, it's supposed, that you make messages using 'form_messages' method.
        Reurns:
            answer (str): Model response in string format.
        """
        json_data = request_openai(messages=messages, **self.openai)
        completion = to_rdict(json_data)
        answer = completion.choices[0].message.content
        return answer
    
    def get_answer(self, messages: list) -> str:
        """
        Wrapper around 'ask' method for case of running out of TPM (tokens per minute) or RPM (requests per minute).
        It is strongly recommended to use this method and not 'ask' one.
        Args:
            messages (list): List of messages (dicts). By default, it's supposed, that you make messages using 'form_messages' method.
        Reurns:
            answer (str): Model response in string format.
        """
        while True:
            try:
                answer = self.ask(messages)
                return answer
            except Exception:
                print(f"[INFO]: TPM/RPM limit exceeded. Waiting {self._sleep_time} seconds to continue requesting.")
                time.sleep(self._sleep_time)

    # Here comes a bunch of prompt wrappings for obtaining an answer of specific type.
    # NOTE: It's not supposed, that you will use this methods manually.
    # Use 'get_' methods instead to obtain a result of a specific type.
    
    def wrap_int(self, request: str) -> str:
        return request + self._wrap_int_string
    
    def wrap_float(self, request: str) -> str:
        return request + self._wrap_float_string
    
    def wrap_prob(self, request: str) -> str:
        return request + self._wrap_prob_string
    
    def wrap_dict(self, request: str) -> str:
        return request + self._wrap_dict_string
    
    def wrap_list(self, request: str) -> str:
        return request + self._wrap_list_string
    
    def wrap_type(self, request: str) -> str:
        """
        EXPERIMENTAL: Wraps request, so that OpenAI API will return the name of type of the answer, that user wants to obtain. May work inaccurately.
        """
        return f"Imagine you get a request: '{request}'. What type of answer does the user expect:{', '.join(self._supported_types)}? Write the dictionary in Python notation as the answer. The dictionary contains {self._n_supported_types} keys (all of them are strings): {', '.join(self._supported_types)}; and values are the probabilities of these types."
    
    def scrub_elem(self, elem: str) -> str:
        """
        Scrubs an element from the list, returned by API as an answer.
        This function strips the elem and then removes it's index from the beginning.
        Example: " 123. Football " -> "Football"
        Args:
            elem (str): Element of the list, obatined by parsing an answer, returned by OpenAI API.
        Returns:
            scrubbed_elm (str): Stripped 'elem' without index in the beginning. 
        """
        return re.sub(r'(?:\d*\.|-)\s*(.*)', r'\1',  elem.strip())
    
    def get_int(self, request: str) -> int:
        """
        Return an API response for the request as an integer.
        Args:
            request (str): Text request to OpenAI API.
        Returns:
            answer (int): OpenAI API response as an integer.
        """
        while True:
            try:
                return int(self.get_answer(self.form_messages(self.wrap_int(request))))
            except Exception:
                pass
    
    def get_float(self, request: str) -> float:
        """
        Return an API response for the request as a float.
        Args:
            request (str): Text request to OpenAI API.
        Returns:
            answer (float): OpenAI API response as a float.
        """
        while True:
            try:
                return float(self.get_answer(self.form_messages(self.wrap_float(request))))
            except Exception:
                pass
    
    def get_prob(self, request: str) -> float:
        """
        Return an API response for the request as a probability (float from 0.0 to 1.0).
        Args:
            request (str): Text request to OpenAI API.
        Returns:
            answer (float): OpenAI API response as a probability.
        """
        while True:
            try:
                answer = self.get_float(request)
                assert 0 <= answer <= 1
                return answer
            except Exception:
                pass
    
    def get_list(self, request: str) -> list:
        """
        Return an API response for the request as a list.
        Args:
            request (str): Text request to OpenAI API.
        Returns:
            answer (list): OpenAI API response as a list.
        """
        while True:
            try:
                return list(map(self.scrub_elem, self.get_answer(self.form_messages(self.wrap_list(request))).split('\n')))
            except Exception:
                pass
    
    def get_dict(self, request: str) -> dict:
        """
        Return an API response for the request as an integer.
        Args:
            request (str): Text request to OpenAI API.
        Returns:
            answer (dict): OpenAI API response as a dict.
        """
        # [TODO]: Add functionallity to process answers with "".
        while True:
            try:
                res_dict = {}
                answer = self.get_answer(self.form_messages(self.wrap_dict(request)))
                # Parse answer string with regexp, so that to get a list of strings with key/value pairs for the dict.
                key_val_array = re.findall(r"'[^']*':[^,]*(?:,|$)", re.sub(r"[\{\}]", "", answer))
                for elem in key_val_array:
                    # Parse each string in list to obtain key/value independently.
                    value = re.sub(r'[,\n]$', '', re.sub(r"'[^']*':\s*", '', elem))
                    key = re.findall(r"'[^']*':", elem)[0][1:-2]
                    res_dict[key] = value
                return res_dict
            except Exception:
                pass
    
    def get_str(self, request: str) -> str:
        """
        Return an API response for the request as a string.
        Args:
            request (str): Text request to OpenAI API.
        Returns:
            answer (str): OpenAI API response as a string.
        """
        return self.get_answer(self.form_messages(request))
    
    def get_type(self, request: str) -> str:
        """
        [EXPERIMENTAL]: Returns the name of type of the answer, that user wants to obtain. May work inaccurately.
        Args:
            request (str): Text request to OpenAI API.
        Returns:
            max_type (str): Predicted name of type of the answer, that user wants to obtain.
        """
        prob_dict = self.get_dict(self.wrap_type(request))
        prob_dict = {key:float(value) for key, value in prob_dict.items()}
        max_type = [type_ for type_ in prob_dict if prob_dict[type_] == max(prob_dict.values())][0]
        return max_type
    
    def __call__(self, request: str) -> Union[int, float, list, dict, str]:
        """
        [EXPERIMENTAL]: Returns an OpenAI API response to request in type, that user wants to obtain. May work inaccurately.
        Args:
            request (str): Text request to OpenAI API.
        Returns:
            answer (Union[int, float, list, dict, str]): OpenAI API answer in a most desired format.
        """ 
        return getattr(self, f'get_{self.get_type(request)}')(request)

    def run(self, request: str) -> str:
        """
        An alias for 'get_str' method for usage as an actor in ChatBot
        """
        return self.get_str(request)

    def __repr__(self):
        """
        Returns an information about the instance of class.
        """
        return self._info

    def __str__(self):
        """
        An alias for '__repr__' method.
        """
        return self.__repr__()
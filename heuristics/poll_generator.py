import json
import re

from ..qagpt import QAGPT


class PollGenerator:
    
    def __init__(self, sphere: str, example: str=None, log: bool=True) -> None:
        if example is not None:
            with open(example, "r", encoding="utf-8") as file:
                self.example = file.read()
        else:
            self.example = ''
        self.sphere = sphere
        self.gpt = QAGPT()
        self.log = log
        self.topics = []
        self.polls = {}
        self.attempts = []
        return
        
    def print(self, *args, **kwargs)-> None:
        if self.log:
            print(*args, **kwargs)
        return
        
    def get_topics(self) -> None:
        request = f"Напиши список основных тем опросников в сфере '{self.sphere}'"
        self.topics = self.gpt.get_list(request)
        nl = '\n'
        self.print(f"[INFO]: Successfully obtained a list of topics for sphere '{self.sphere}'")
        self.print(f"Here they are:\n{nl.join(self.topics)}")
        return
        
    def run(self, output: bool=False) -> None:
        self.attempts.clear()
        self.get_topics()
        for topic in self.topics:
            while True:
                request = f"""
                    Напиши опрос на тему {topic}.
                    Опрос должен состоять из 7 вопросов.
                    Вкаждом вопросе должно быть 3-4 варианта ответа.
                    Опрос должен быть представлен в формате JSON.
                    Каждый ключ в JSON-файле должен быть внутри двойных кавычек.
                    Пример формата указан ниже:
                    {self.example}
                """
                answer = self.gpt.get_str(request)
                self.attempts.append(answer)
                new_answer = re.sub(r"\s+", " ", answer)
                try:
                    poll = json.loads(new_answer)
                    self.polls[topic] = poll
                    self.print(f"[INFO]: Successfully created poll on topic: '{topic}'")
                    if output:
                        self.to_json(topic, f"{topic}.json")
                    break
                except Exception as e:
                    self.print(f"[ERROR]: An exception has occured during generation poll on topic '{topic}'.")
                    self.print(f"'{e}'. Retrying...")
        self.print(f"[INFO]: Finished generating polls for sphere: '{self.sphere}'.")
        return
            
    def to_json(self, topic: str, path: str) -> None:
        if topic not in self.polls:
            return
        with open(path, "w") as json_file:
            json.dump(self.polls[topic], json_file)
        self.print(f"[INFO]: Successfully written poll '{topic}' into a file: '{path}'")
        return
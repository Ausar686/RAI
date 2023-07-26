import json


class Poll:
    
    _bot = "[RBot]"
    
    def __init__(self, json_path: str) -> None:
        self.poll = None
        self.load(json_path)
        self.user_answers = {}
        self.joiner = '\n\t'
        self.instructions = f"""
            <INSTRUCTIONS>
            Write a conclusion about my current condition, using the information below.
            Your answer should be provided in Russian language.
            Use "ты" in order to address to me.
            <CONTEXT>
            """
        self._str = self.to_str()
        
    def load(self, json_path: str) -> None:
        with open(json_path, "r") as json_file:
            self.poll = json.load(json_file)
        return
    
    def run(self) -> None:
        for elem in self.poll:
            question, variants, answers = self.unpack(elem)
            self.display(question, answers)
            user_answer = self.input()
            self.user_answers[question] = user_answer
            try:
                index = answers.index(user_answer)
            except ValueError:
                index = -1
            if index < 0:
            # Improve this in further updates.
                func_name = variants[-1]["call"]["name"]
                eval(f"self.{func_name}()")
                continue
            variant = variants[index]
            reply = variant.get("reply")
            if reply:
                print(f"{self._bot}: {reply}")
            call = variant.get("call")
            if call:
                func_name = call.get("name")
                kwargs = call.get("kwargs")
                if kwargs:
                    eval(f"self.{func_name}(**{kwargs})")
                else:
                    eval(f"self.{func_name}()")
                continue
        self.instructions += str(self.user_answers)
        return
                
    def unpack(self, elem: dict) -> tuple:
        question = elem["question"]
        variants = elem["variants"]
        answers = [variant["answer"] for variant in variants if variant["answer"]]
        return (question, variants, answers)
    
    def format(self, question: str, answers: list) -> str:
        return f"{question}{self.joiner}{self.joiner.join([f'{i+1}.{answer}' for i, answer in enumerate(answers)])}"
                
    def display(self, question: str, answers: list) -> None:
        print(f"{self._bot}: {self.format(question, answers)}")
        return
                
    def input(self) -> str:
        return input("[User]: ")
    
    def to_str(self) -> str:
        res = ''
        for elem in self.poll:
            question, variants, answers = self.unpack(elem)
            res += self.format(question, answers) + '\n'
        return res

    def analyse_input(self) -> None:
        print(f"{self._bot}: Я только учусь воспринимать человеческий текст. Я записал твой ответ, но, пожалуйста, постарайся в будущем отвечать, используя предоставленные варианты.")

    def ask_condition(self, condition: str) -> None:
        print(f"{self._bot}: Ты сейчас испытываешь состояние '{condition}'\n\tРасскажи, пожалуйста, поподробнее.")
        descr = input("[User]: ")
        print(f"{self._bot}: Спасибо! Я подумаю, как тебе помочь...")
        return
    
    def __repr__(self) -> str:
        return self._str
    
    def __str__(self) -> str:
        return str(self.poll)
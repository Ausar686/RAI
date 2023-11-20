# Features
Another important feature of this library is **QAGPT** (Question/Answer GPT) class.
QAGPT provides you an interface for asking single questions and obtaining structured answers (like lists, int, floats, strings, etc.)
Currently these types are supported:
- **int**
- **float**
- **str**
- **prob** (probability; float from 0 to 1)
- **list**
- **dict** (BETA)

# Usage
## Initialize QAGPT
To begin with, let's create a QAGPT instance.
```python
from RAI import QAGPT
gpt = QAGPT()
```
In basic case you want to setup these parameters:
- **model** - OpenAI Model (str)
- **key** - OpenAI API key (str)
- **temperature** - Model temperature (float)

You can get more information about these parametes on [official OpenAI website](https://platform.openai.com/docs/api-reference/chat/create?lang=python).
> **Note:** As in ChatBot, you don't need to explicitly pass your API key. 
If **key** is not set, your "**OPENAI_API_KEY**" environment variable will be taken instead. 

## Asking questions
Assuming, that you have your question, presented as **str**, you can get the answer of type *dtype* by simply calling method **get_*dtype***, replacing *dtype* with your actual desired data type.
For example, consider the following scenario: we want to get a list of all European countries.
To do this, using our QAGPT instance we can write the following:
```python
question = "Write list of all European countries"
answer = gpt.get_list(question)
type(answer)
>>> list
```

If you want to get a string, you an use **run** method as a shortcut:
```python
question = "Write a story for my son"
answer = gpt.run(question)
type(answer)
>>> str
```

## Memory
Take a note, that QAGPT **does not** remember your previous questions.
It only provides an answer to a single input, given as the only argument to **get_...** methods.

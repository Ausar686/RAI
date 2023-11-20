# Usage (Basic)
## Initialize ChatBot
Main feature, implemented in this library, is a ChatBot, which one can use in either console or jupyter notebook interface.
First of all, let's import the ChatBot class:
```python
from RAI import ChatBot
bot = ChatBot("/path/to/config/file.json")
```
We pass one argument: a path to a bot configuration file. This configuration file determines the parameters of the LLM (i.e. model name, temperature, etc.), as well as bot's instructions. Here is an example of a configuration file one can use for his own purposes:
```json
{
	"root": null,
	"openai": {
		"api_key": "YOUR_KEY_HERE"
	},
	"instructions": {
		"role": "Act as an experienced software developer.",
		"format": "Your messages should end with a relevant question to keep the conversation going.",
		"efficiency": "Each token matters, so keep your messages precise and concise.",
		"hello": "Start a conversation with a short greeting."
	}
}
```

Let's go through this configuration file step-by-step:
## 1. Root 
This keyword specifies the path to another configuration file, which should be considered first. 
- If **root** is not null, ChatBot will firstly inspect the file, specified in **root** section and store all data from it.
- Secondly, ChatBot will inspect current configuration file and unite the sections from both files.
- If there are any intersections in sections' names among configuration files, the latest
(the one, which is the most distant from root) file's sections' values will be considered as ChatBot values.

This section is useful for inheritance purposes, when you want to specify basic set of parameters
(like LLM model, temperature and some general instructions) and then specify only a few instructions for each individual ChatBot.
> **Note:** Root section must be specified **explicitly** in **each** configuration file, even when it's value is **null**.

## 2. OpenAI
This keyword specifies parameters of OpenAI LLMs, as well as your personal OpenAI API key.
For detailed review of parameters' list check out this link:
https://platform.openai.com/docs/api-reference/chat/create?lang=python
> **Note:** OpenAI section should be presented in at least one of the configuration files in your config chain. Otherwise, ValueError Exception will be raised.

> **Note:** You do not have to set API key explicitly in config file, or even write "api_key": null in this section. If you don't present an API key in file, ChatBot will take it from your environment variable "OPENAI_API_KEY". If this variable is not set, ChatBot will set your internal API key to None.

## 3. Instructions
This keyword specifies dictionary with instructions to a ChatBot, which are sent to him as a first message in a conversation, using "system" role. 
You can learn more about roles in OpenAI API by checking out the link above (in OpenAI section).
Basically, each instruction is represented in configuration file as a key-value pair, where key is a name of an instruction, and value is the instruction itself.
> **Note:** Instructions' names are not used by ChatBot. They are presented only for user's comfort.

> **Note:** Generally speaking, you should be able to put any required for your purposes instructions.
However, there are some token limitations for different GPT models in OpenAI API. 
For more info check out this link: https://platform.openai.com/docs/models

## Run a conversation
To start a conversation with a ChatBot simply use **run** method:
```python
bot.run()
```
The conversation will keep going until you give an empty input (simply press **Enter** when it's your turn in dialog).
> **Note:** For several reasons there was a postprocessing added to ChatBot, so that it converts mostly all numerated lists into plain text.
However, sometimes this feature fails and you can see some digits inside the plain text. This issue will be resolved in the future.


# Usage (Advanced)
For several purposes one may consider an option of using ChatBot interface in his own applications.
However, basic implementation assumes, that ChatBot receives input from a standard input and writes output into standard output,
which is not convinient, for example, for bot-vs-bot interactions.
In order to support this feature we present some inheritance tips to reuse general pipeline of a ChatBot in your own applications:
- Override **input** method
- Override **process_output** method

## Override input
The signature of the **input** method is presented as following:
```python
def input(self, *args, **kwargs) -> Message:
```
Message is an individual class in RAI to send, receive and store data and metadata in user and bot messages.
We will not dive into details of internal implementation of a Message class here.
Basically, to turn raw text, stored in Python variable **content** to a message you need to use:
```python
msg = self.user_message(content)
```
to convert content to a message from user. 
If you want to convert to either system or assistant (bot itself) message, you can use the following:
```python
msg = self.system_message(content)
msg = self.bot_message(content)
```
In these examples **self** is a reference to ChatBot (or subclass) instance.

To sum up, in your overriden method there should be:
- Content obtaing (should return str)
- Content conversion to Message (gets str as input returns Message as output) 

## Override output
The signature of the **process_output** method is presented as following:
```python
def process_output(self, *args, **kwargs) -> None:
```
In ChatBot it does the following:
- Gets answer from LLM (**get_answer** method) as Message
- Appends Message to internal ChatBot storage (**append** method)
- Displays message's content (**display** method)

In order to keep things working you have to implement the same logic in your custom subclass. 
We strongly **do not** recommend to override **get_answer** and **apend** methods, as it can break the entire workflow.

## Test your subclass
When you are finished, you can check your subclass, as presented in example below:
```python
class MyBot(ChatBot):
    # YOUR_CODE_HERE

bot = MyBot(/path/to/config/file.json)
bot.run()
```

If you want to use 2 bots communicating with each other, you may need something like this:
```python
bot1 = MyBot("/path/to/config/file1.json")
bot2 = MyBot("/path/to/config/file2.json")
while True: # YOUR_CONDITION_HERE
    # Bot1 message
    bot1.process_output()
    bot2.process_input(bot_chef.last_message.content)
    bot1.verify_context()
    bot2.verify_context()
    # Bot2 message
    bot2.process_output()
    bot1.process_input(bot_user.last_message.content)
    bot2.verify_context()
    bot1.verify_context()
```

## Save the dialog
If you want to save the dialog in .txt format use **to_txt** method of ChatBot.
This method takes one argument: path to the output file.
```python
def to_txt(self, path: str) -> None:
```
> **Note:** This method will raise an Exception if some of directories in path to file do not exist.

## Clear dialog history with current bot
To clear dialog context (but **NOT** the entire chat) with current bot use **clear** method. It takes no arguments:
```
bot.clear()
```

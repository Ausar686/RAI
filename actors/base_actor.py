# Created by: Ausar686
# https://github.com/Ausar686

class BaseActor:
	"""
	Base class for all RAI actors, which can be used in ChatBot
	"""

	def __init__(self, model: str="gpt-3.5-turbo"):
		"""
		Initialize an actor.
		"""
		self.set_model(model)
		return

	def set_model(self, model: str) -> None:
		"""
		Set actor's model.
		"""
		self.model = model
		return

	def run(self):
		"""
		Override this method for every subclass in order to use it properly as an actor in ChatBot.
		"""
		pass
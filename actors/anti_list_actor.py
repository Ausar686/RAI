# Created by: Ausar686
# https://github.com/Ausar686

from .qagpt import QAGPT


class AntiListActor(QAGPT):

	_prompt = """
		###INSTRUCTIONS###
		Inspect the text below.
		If there is a numerated list in text write only the first element of the list, explained in detail, according to context.
		Keep everything else (except of numerated list) exactly the same, as the original.
		Keep the same language, as the original.
		Keep the same style, as the original.
		Example:
			Input: 
				There are multiple sports, that can suit you. Here are several examples:
					1. Football
					2. Hockey
					3. Basketball
					4. Volleyball
					5. Tennis
				It's crucial to choose a sport, according to personal preferences. What do you think about it?
			Output:
				There are multiple sports, that can suit you. For example, football is a decent solution because of your outstanding stamina. What do you think about it?

		###TEXT###
	"""

	def run(self, text: str) -> str:
		request = f"{self._prompt}{text}"
		result = self.get_str(request)
		enum_str = "\n\n1."
		index = result.find(enum_str)
		if index >= 0:
			result = result[:index] + result[index+len(enum_str)+1:]
		return result
from .base_actor import BaseActor
from .qagpt import QAGPT
from ..api_pmc_requests import PMCRequester

class KnowledgeBaseSearcher(BaseActor):
    
    _defaults = {
        "ip": "83.220.174.161",
        "port": "9202",
        "prompt": f"Напиши названия 10 статей PubMed Central, в которых подтверждаются следующие слова:\n",
        "url_prefix": "https://pubmed.ncbi.nlm.nih.gov/",
        "descr": "Подробнее об этом можно прочитать в статьях:\n"
    }
    
    def __init__(
        self, 
        model: str="gpt-3.5-turbo",
        *, 
        ip: str=None,
        port: str=None,
        prompt: str=None,
        url_prefix: str=None):
        """
        Initializes an instance of the class
        Args:
            model [str]: GPT model. Available: "gpt-3.5-turbo", "gpt-4". Default: "gpt-3.5-turbo".
        Kwargs:
            ip [str]: Knowledge base IP for PMCR. If None is passed, uses Heuristics PMC IP. Default: None.
            port [str]: Knowledge base port for PMCR. If None is passed, uses Heuristics PMC port. Default: None.
            prompt [str]: Prompt to generate relevant articles' titles. If None is passed, uses default prompt. Default: None.
            url_prefix [str]: URL prefix for URL-generation from PMID (PMC-specific). If Non is passed, uses default prefix. Default: None.
        """
        # Initialize required parameters
        super().__init__(model)
        if ip is None:
            self.ip = self._defaults["ip"]
        else:
            self.ip = ip
        if port is None:
            self.port = self._defaults["port"]
        else:
            self.port = port
        if prompt is None:
            self.prompt = self._defaults["prompt"]
        else:
            self.prompt = prompt
        # Initialize PMC-specific parameters
        self.url_prefix = self._defaults["url_prefix"]
        self.descr = self._defaults["descr"]
        # Initialize GPT instance
        self.gpt = QAGPT(self.model)
        # Initialize PMCR instance
        self.pmc = PMCRequester(ip_address=self.ip, port=self.port)
        return
    
    def wrap(self, text: str) -> str:
        """
        Wrap an input string to further address it to OpenAI API.
        """
        return f"{self.prompt}{text}"
    
    def generate(self, text: str=None) -> list:
        """
        Generates names of the relevant articles with QAGPT.
        """
        if text is None or text == "":
            return []
        request = self.wrap(text)
        articles = self.gpt.get_list(request)
        return articles
    
    def filter(self, articles: list=None) -> list:
        """
        Filters generated names of the articles with PMCRequester.
        Returns a list of tuples: (article_title, article_url)
        """
        if articles is None or articles == []:
            return []
        filtered_articles = []
        for article in articles:
            title, pmid = self.pmc.find_title(article)
            if title is not None:
                url = self.url_prefix + pmid
                filtered_articles.append((title, url))
        return filtered_articles
    
    def to_json(self, text: str=None, filtered_articles: list=None) -> dict:
        """
        Converts search results into JSON format.
        """
        if text is None or text == "":
            return {}
        if filtered_articles is None or filtered_articles == []:
            return {"text": text, "descr": self.descr, "article": []}
        return {
            "text": text, 
            "descr": self.descr, 
            "article": [{"title": title, "url": url} for (title, url) in filtered_articles]
        }
    
    def run(self, text: str=None) -> dict:
        """
        Executes full pipeline: 
            1. Generates relevant article titles with QAGPT
            2. Filters generated titles with PMCR
            3. Converts the results into JSON format (Python dict)
        """
        articles = self.generate(text)
        filtered_articles = self.filter(articles)
        json_data = self.to_json(text, filtered_articles)
        return json_data
    
    @staticmethod
    def to_str(json_data: dict) -> str:
        """
        Converts the result of 'run' method into string format for further display to user.
        """
        text = json_data.get("text", "").strip() + "\n"
        descr = json_data.get("descr", "").strip() + "\n\n"
        articles = json_data.get("article", [])
        article_str = ""
        for i, article in enumerate(articles, start=1):
            article_str += f"{i}.{article.get('title', '')}\n{article.get('url', '')}\n\n"
        res = f"{text}{descr}{article_str}"
        return res
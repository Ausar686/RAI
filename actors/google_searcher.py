# Created by: Ausar686
# https://github.com/Ausar686

from bs4 import BeautifulSoup
import requests
import urllib


class GoogleSearcher:
    """
    RAI class, that implements Web browsing 
    via Google Search Engine.
    """
    
    def __init__(self):
        """
        Initializes instance with attributes to store data
        for debugging.
        """
        self.clear()
        self.google = "https://google.com/search"
        self.prefix = "/url?q="
        self.suffix = "&sa="
        
    def get_response(self, query: str) -> requests.Response:
        """
        Gets response from GET requestto Google Search Engine.
        """
        # Set query parameter
        params = {"q": query}
        # Get response from Google Search
        resp = requests.get(self.google, params=params)
        # Save response to 'resp' attribute
        self.resp = resp
        return resp
    
    def fetch_urls(self, resp: requests.Response) -> list:
        """
        Fetches urls from response, using BeautifulSoup from bs4 library.
        """
        # Get response content as text (not binary)
        content = resp.text
        # Parse the content using BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        # Extracting URLs based on the provided structure
        search_result_anchors = soup.find_all('a')
        # Getting the href attribute from these anchors
        page_urls = [a['href'] for a in search_result_anchors]
        # Getting urls, that start with "/url?q="
        result_urls = [url.split(self.prefix)[-1] for url in page_urls if url.startswith(self.prefix)]
        return result_urls
    
    @staticmethod
    def is_google_url(url: str) -> bool:
        """
        Checks, whether the URL is not a result of search,
        and is a Google URL instead 
        """
        return (
            url.find("support.google.com") >= 0 or
            url.find("accounts.google.com") >= 0)
    
    def postprocess_urls(self, urls: list) -> list:
        """
        Performs URLs postprocessing, so that to return clear urls,
        which are ready-to-use by end user.
        """
        # Strip urls
        stripped_urls = [url[:url.find(self.suffix)] if url.find(self.suffix) != -1 else url for url in urls]
        # Unquote urls
        unquoted_urls = [urllib.parse.unquote(url) for url in stripped_urls]
        # Remove all results with support.google.com and accounts.google.com
        cleared_urls = [url for url in unquoted_urls if not self.is_google_url(url)]
        self.urls = cleared_urls
        return cleared_urls
    
    def clear(self) -> None:
        """
        Clears previous results (self.resp and self.urls)
        """
        self.resp = None
        self.urls = None
        return
    
    def search(self, query: str) -> list:
        """
        Runs a full search pipeline: 
        1. 'get_response'
        2. 'fetch_urls'
        3. 'postprocess_urls'
        """
        r = self.get_response(query)
        if r.status_code == 200:
            urls = self.fetch_urls(r)
            urls = self.postprocess_urls(urls)
            return urls
        else:
            print(f"[ERROR]: URL: {r.url} STATUS: {r.status_code}")
            return None
    
    def run(self, query: str) -> list:
        """
        An alias for 'search' method for compatibility with other actors
        """
        return self.search(query)
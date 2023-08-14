from .pmc_models import ModelPMC, ModelPubMedLine
import orjson
import requests
from requests.utils import quote
from pydantic import parse_obj_as

class Singleton(type):
  _instances = {}
  def __call__(cls, *args, **kwargs):
      if cls not in cls._instances:
          instance = super().__call__(*args, **kwargs)
          cls._instances[cls] = instance
      return cls._instances[cls]
  
class PMCRequester(metaclass=Singleton):
    """
    The `ModelPMC` instance is constructed by invoking its constructor with arguments that are parsed from the `source` dictionary 
    using the `parse_obj_as` function. The `parse_obj_as` function takes two arguments: a type hint for the expected data type, 
    and the actual data. It returns the parsed object if parsing succeeds, or raises an error if parsing fails. 
    The `ModelPMC` class is defined somewhere else in the code and likely contains data attributes 
    that correspond to the keys in the `source` dictionary.
    """
    def __init__(self, ip_address: str, port: str):
        """
        Instance of API
        """
        self.host = ip_address
        self.port = port
        self.session = requests.Session()
    
    def toQuartileNumber(self, Q1: bool, Q2: bool, Q3:bool, Q4:bool, Qnan:bool) -> int:
        """
        get Quartile Number from bool values.
        """
        bitQ1, bitQ2, bitQ3, bitQ4, bitQnan = int(not Q1), int(not Q2), int(not Q3), int(not Q4), int(not Qnan)
        return bitQnan * 2**0 + bitQ4 * 2**1 + bitQ3 * 2**2 + bitQ2 * 2**3 + bitQ1 * 2**4

    #pubmed
    def find_title(self, text: str, threshold: int = 0, default: str = None, 
                   filter_quartile: int = 0, filter_country: str = None) -> str:
        """
        Search Title top-1 comparison with max score.
        """
        URL = f'http://{self.host}:{self.port}/pubmed/title/{quote(text)}?size=1&filter_quartile={str(filter_quartile)}'
        if filter_country is not None:
            URL += f'&filter_country={quote(filter_country)}'
        response = self.session.get(URL)
        if response.status_code == 200:
            result = orjson.loads(response.content)
            max_score = self.__float(result.get('max_score'))
            if max_score >= threshold:
                try:
                    return result.get('hits')[0].get('_source').get('MedlineCitation').get('Article').get('ArticleTitle', default), result.get('hits')[0].get('_id', default)
                except Exception:
                    return default, default
        return default, default
    
    #pubmed
    def find_titles_top5(self, text: str, threshold: int = 0, default: str = None) -> list:
        """
        Search Title top-5 comparisons ordered by score DESC.
        """
        URL = f'http://{self.host}:{self.port}/pubmed/title/{quote(text)}'
        response = self.session.get(URL)
        if response.status_code == 200:
            result = orjson.loads(response.content)
            max_score = self.__float(result.get('max_score'))
            if max_score >= threshold:
                retlist = []
                array = result.get('hits', [])
                for hit in array:
                    try:
                        score = self.__float(hit.get('_score'))
                        if score >= threshold:
                            title = hit.get('_source').get('MedlineCitation', {}).get('Article', {}).get('ArticleTitle', default)
                            if title not in retlist:
                                retlist.append(title)
                    except Exception:
                        return []
                return retlist
        return []

    #pubmed
    def pubmed_articles(self, text: str, pageNumber: int, size:int=20, default = None,
                     filter_quartile: int = 0, filter_country: str = None):
        """
        Default return is None. 
        """
        URL = f'http://{self.host}:{self.port}/pubmed/articles/{quote(text)}?size={str(size)}&page={str(pageNumber)}&filter_quartile={str(filter_quartile)}'
        if filter_country is not None:
            URL += f'&filter_country={quote(filter_country)}'
        response = self.session.get(URL)
        if response.status_code == 200:
            return orjson.loads(response.content)
        return default

    #PMC
    def pmc_articles(self, text: str, pageNumber: int, size:int=20, default = None,
                     filter_quartile: int = 0, filter_country: str = None):
        """
        Default return is None. 
        """
        URL = f'http://{self.host}:{self.port}/pmc/articles/{quote(text)}?size={str(size)}&page={str(pageNumber)}&filter_quartile={str(filter_quartile)}'
        if filter_country is not None:
            URL += f'&filter_country={quote(filter_country)}'
        response = self.session.get(URL)
        if response.status_code == 200:
            return orjson.loads(response.content)
        return default
    
    #PMC
    def aggs_date_year(self, default = None) -> list:
        """
        Default return is None. 
        """
        URL = f'http://{self.host}:{self.port}/pmc/count/last30years'
        response = self.session.get(URL)
        if response.status_code == 200:
            return orjson.loads(response.content)
        return default
    
    #PMC
    def get_byid(self, text: str, default = None):
        """
        Default return is None. 
        """
        URL = f'http://{self.host}:{self.port}/pmc/article/{quote(text)}'
        response = self.session.get(URL)
        if response.status_code == 200:
            return orjson.loads(response.content)         
        return default
    
    def pd_Series_get_byid(self, text: str, default = None):
        """
        return pandas.DataFrame if ModelPMC() else return Default is None.
        """
        model = self.__get_pmc_model(self.get_byid(text))
        if model is not None:
            return model.dataframe_dict_1d()
        return default

    #pmc
    def pd_DataFrame_pmc_articles(self, text: str, pageNumber: int, size:int=20, default = None,
                                  filter_quartile: int = 0, filter_country: str = None):
        content = self.pmc_articles(text, pageNumber, size, filter_quartile=filter_quartile, filter_country=filter_country)
        if content:
            count = int(content.get('total', {}).get('value', 0))
            array = []
            for hit in content.get('hits', []):
                source_dict = hit.get('_source', {})
                model = self.__get_pmc_model(source_dict)
                if model is not None:
                    array.append(model.dataframe_dict_1d())
            return array, count
        return default, 0
    
    #pubmed
    def pd_DataFrame_Pubmed_articles(self, text: str, pageNumber: int, size:int=20, default = None,
                                  filter_quartile: int = 0, filter_country: str = None):
        content = self.pubmed_articles(text, pageNumber, size, filter_quartile=filter_quartile, filter_country=filter_country)
        if content:
            count = int(content.get('total', {}).get('value', 0))
            array = []
            for hit in content.get('hits', []):
                source_dict = hit.get('_source', {})
                model = self.__get_pubmed_model(source_dict)
                if model is not None:
                    array.append(model.dataframe_dict_1d())
            return array, count
        return default, 0
    
    def __get_pmc_model(self, source: dict, default = None):
        """
        return ModelPMC() if parse_obj_as(source) else return Default is None.
        The `__get_class_validated_from_source` method takes a dictionary `source` representing a PMC article 
        and returns an instance of the `ModelPMC` class that is populated with the values from the `source` dictionary. 
        If the `source` dictionary cannot be parsed into a valid `ModelPMC` instance, 
        the method returns the value of the `default` parameter, which is set to `None` by default.

        """
        try:
            return ModelPMC(
                journal = parse_obj_as(ModelPMC.JournalModel, source.get('journal')),
                PMID = source.get('PMID', 0),
                PMCID = source.get('PMCID'),
                DOI = source.get('DOI'),
                Title = source.get('Title'),
                Author = parse_obj_as(list[ModelPMC.AuthorModel], source.get('Author')),
                date = parse_obj_as(ModelPMC.DateModel, source.get('date')),
                date_epub = source.get('date_epub'),
                Abstract = source.get('Abstract'),
                Text_full = source.get('Text_full'),
                Glossary = parse_obj_as(list[ModelPMC.DefinitionModel], source.get('Glossary')),
                Categories = source.get('Categories'),
                Affiliations = parse_obj_as(list[ModelPMC.InstituteModel], source.get('Affiliations')),
                book = parse_obj_as(ModelPMC.BookModel, source.get('book')),
                Ref_ids = parse_obj_as(list[ModelPMC.PubmedidModel], source.get('Ref_ids')),
                References = parse_obj_as(list[ModelPMC.PaperModel], source.get('References'))
            )
        except Exception:
            return default
        
    def __get_pubmed_model(self, source: dict, default = None):
        """
        return ModelPubMedLine() if parse_obj_as(source) else return Default is None.
        The method takes a dictionary `source` representing a Pubmed article 
        and returns an instance of the `ModelPubMedLine` class that is populated with the values from the `source` dictionary. 
        If the `source` dictionary cannot be parsed into a valid `ModelPubMedLine` instance, 
        the method returns the value of the `default` parameter, which is set to `None` by default.

        """
        try:
            MedlineCitationDict = source.get('MedlineCitation')
            ArticleDict = MedlineCitationDict.get('Article')
            JournalDict = ArticleDict.get('Journal')
            JournalIssueDict = JournalDict.get('JournalIssue', {})
            PubmedDataDict = source.get('PubmedData')
            return ModelPubMedLine(
                MedlineCitation = ModelPubMedLine.MedlineCitationModel(
                    PMID = MedlineCitationDict.get('PMID'),
                    DateRevised = parse_obj_as(ModelPubMedLine.MedlineCitationModel.DateRevisedModel, MedlineCitationDict.get('DateRevised', {})),
                    Article = ModelPubMedLine.MedlineCitationModel.ArticleModel(
                        Journal = ModelPubMedLine.MedlineCitationModel.ArticleModel.JournalModel(
                            ISOAbbreviation = JournalDict.get('ISOAbbreviation'),
                            Title = JournalDict.get('Title'),
                            JournalIssue = ModelPubMedLine.MedlineCitationModel.ArticleModel.JournalModel.JournalIssueModel(
                                Volume = JournalIssueDict.get('Volume', ''),
                                Issue = JournalIssueDict.get('Issue', ''),
                                PubDate = parse_obj_as(ModelPubMedLine.MedlineCitationModel.ArticleModel.JournalModel.JournalIssueModel.PubDateModel, JournalIssueDict.get('PubDate', {})),
                            ),
                            ISSN_Print = JournalDict.get('ISSN_Print'),
                            ISSN_Electronic = JournalDict.get('ISSN_Electronic'),
                        ),
                        ArticleTitle = ArticleDict.get('ArticleTitle'),
                        Pagination = ArticleDict.get('Pagination', ''),
                        ELocationID = parse_obj_as(list[ModelPubMedLine.MedlineCitationModel.ArticleModel.ELocationIDModel], ArticleDict.get('ELocationID', [])),
                        AbstractText = parse_obj_as(list[ModelPubMedLine.MedlineCitationModel.ArticleModel.AbstractTextModel], ArticleDict.get('AbstractText', [])),
                        CopyrightInformation = ArticleDict.get('CopyrightInformation', ''),
                        AuthorList = parse_obj_as(list[ModelPubMedLine.MedlineCitationModel.ArticleModel.AuthorModel], ArticleDict.get('AuthorList', [])),
                        PublicationTypeList = parse_obj_as(list[ModelPubMedLine.MedlineCitationModel.ArticleModel.PublicationTypeModel], ArticleDict.get('PublicationTypeList', [])),
                    ),
                    MedlineJournalInfo = parse_obj_as(ModelPubMedLine.MedlineCitationModel.MedlineJournalInfoModel, MedlineCitationDict.get('MedlineJournalInfo')),
                    MeshHeadingList = parse_obj_as(list[ModelPubMedLine.MedlineCitationModel.MeshHeadingModel], MedlineCitationDict.get('MeshHeadingList', [])),
                    KeywordList = parse_obj_as(list[ModelPubMedLine.MedlineCitationModel.KeywordModel], MedlineCitationDict.get('KeywordList', [])),
                    CommentsCorrectionsList = parse_obj_as(list[ModelPubMedLine.MedlineCitationModel.CommentsCorrectionsModel], MedlineCitationDict.get('CommentsCorrectionsList', [])),
                    ChemicalList = parse_obj_as(list[ModelPubMedLine.MedlineCitationModel.ChemicalModel], MedlineCitationDict.get('ChemicalList', [])),
                ),
                PubmedData = ModelPubMedLine.PubmedDataModel(
                    History = parse_obj_as(list[ModelPubMedLine.PubmedDataModel.PubMedPubDateModel], PubmedDataDict.get('History')),
                    ArticleIdList = parse_obj_as(list[ModelPubMedLine.PubmedDataModel.ArticleIdModel], PubmedDataDict.get('ArticleIdList')),
                    ReferenceList = parse_obj_as(list[ModelPubMedLine.PubmedDataModel.ReferenceModel], PubmedDataDict.get('ReferenceList', [])),
                ),
                DateEntrez = source.get('DateEntrez')
            )
        except Exception:
            return default

    def __float(self, x):
        """
        The `__float` method is a private helper method that takes a value `x` and attempts to parse it as a floating-point number. 
        If parsing succeeds, the method returns the float value of `x`. If parsing fails, the method returns 0. 
        The double underscores in the method name indicate that it is meant to be a private method.
        """
        try:
            return float(x)
        except Exception:
            return 0
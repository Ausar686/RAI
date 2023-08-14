from pydantic import BaseModel
from pydantic import parse_obj_as
# Python >= 3.9 version required

#PMC
class ModelPMC(BaseModel):
    """
    Serializable model of /index of OpenSearch
    """
    class JournalModel(BaseModel):
        nlm: str = ''
        longname: str = ''
        ISSNP: str = ''
        ISSNE: str = ''

    class DateModel(BaseModel):
        year: int
        month: int = 0
        day: int = 0

    class AuthorModel(BaseModel):
        fullname: str = ''
        initials: str = ''

    class DefinitionModel(BaseModel):
        definition: str = ''

    class InstituteModel(BaseModel):
        institute: str = ''

    class BookModel(BaseModel):
        volume: str = ''
        issue: str = ''
        first_page: str = ''
        last_page: str = ''

    class PubmedidModel(BaseModel):
        pubmed_id: int

    class PaperModel(BaseModel):
        paper: str = ''

    # @properties
    journal: JournalModel
    PMID: int = 0
    PMCID: str
    DOI: str = ''
    Title: str = ''
    Author: list[AuthorModel] = []
    date: DateModel
    date_epub: str
    Abstract: str = ''
    Text_full: str = ''
    Glossary: list[DefinitionModel] = []
    Categories: str = ''
    Affiliations: list[InstituteModel] = []
    book: BookModel
    Ref_ids: list[PubmedidModel] = []
    References: list[PaperModel] = []

    def dataframe_dict_1d(self):
        __list__Author_fullname = []
        __list__Author_initials = []
        __list__Glossary = []
        __list__Affilations = []
        __list__Refids = []
        __list__References = []
        
        for author in self.Author:
            __list__Author_fullname.append(author.fullname)
            __list__Author_initials.append(author.initials)
        for glossary in self.Glossary:
            __list__Glossary.append(glossary.definition)
        for affiliation in self.Affiliations:
            __list__Affilations.append(affiliation.institute)
        for refid in self.Ref_ids:
            __list__Refids.append(str(refid.pubmed_id))
        for reference in self.References:
            __list__References.append(reference.paper)

        return {
            "PMID": self.PMID,
            "PMCID": self.PMCID,
            "Title": self.Title,
            "Categories": self.Categories,
            "date_epub": self.date_epub,
            "Abstract": self.Abstract,
            "Author.initials": ", ".join(__list__Author_initials),
            "Author.fullname": ", ".join(__list__Author_fullname),
            "Affiliations": "; ".join(__list__Affilations),
            "Text_full": self.Text_full,
            "Glossary": "; ".join(__list__Glossary),
            "journal.nlm": self.journal.nlm,
            "journal.longname": self.journal.longname,
            "journal.ISSNP": self.journal.ISSNP,
            "journal.ISSNE": self.journal.ISSNE,
            "DOI": self.DOI,
            "book.volume": self.book.volume,
            "book.issue": self.book.issue,
            "book.first_page": self.book.first_page,
            "book.last_page": self.book.last_page,
            "date.year": self.date.year,
            "date.month": self.date.month,
            "date.day": self.date.day,
            "Ref_ids": ",".join(__list__Refids),
            "References": "\n".join(__list__References),
        }
    
    @classmethod
    def from_source(self, source: dict, default = None):
        try:
            return self(
                journal = parse_obj_as(self.JournalModel, source.get('journal')),
                PMID = source.get('PMID', 0),
                PMCID = source.get('PMCID'),
                DOI = source.get('DOI'),
                Title = source.get('Title'),
                Author = parse_obj_as(list[self.AuthorModel], source.get('Author')),
                date = parse_obj_as(self.DateModel, source.get('date')),
                date_epub = source.get('date_epub'),
                Abstract = source.get('Abstract'),
                Text_full = source.get('Text_full'),
                Glossary = parse_obj_as(list[self.DefinitionModel], source.get('Glossary')),
                Categories = source.get('Categories'),
                Affiliations = parse_obj_as(list[self.InstituteModel], source.get('Affiliations')),
                book = parse_obj_as(self.BookModel, source.get('book')),
                Ref_ids = parse_obj_as(list[self.PubmedidModel], source.get('Ref_ids')),
                References = parse_obj_as(list[self.PaperModel], source.get('References'))
            )
        except Exception:
            return default

#PubMedLine
class ModelPubMedLine(BaseModel):
    """
    Serializable model: Pubmed/MEDLINE
    """
    class MedlineCitationModel(BaseModel):
        class DateRevisedModel(BaseModel):
            Year: str
            Month: str
            Day: str
        class ArticleModel(BaseModel):
            class JournalModel(BaseModel):
                class JournalIssueModel(BaseModel):
                    class PubDateModel(BaseModel):
                        Year: str = ''
                        Month: str = ''
                        Day: str = ''
                    Volume: str = ''
                    Issue: str = ''
                    PubDate: PubDateModel
                ISOAbbreviation: str
                Title: str
                JournalIssue: JournalIssueModel
                ISSN_Print: str = ''
                ISSN_Electronic: str = ''
            class AuthorModel(BaseModel):
                class AffiliationModel(BaseModel):
                    Affiliation: str = ''
                LastName: str = ''
                ForeName: str = ''
                Initials: str = ''
                AffiliationInfo: list[AffiliationModel] = []
            class ELocationIDModel(BaseModel):
                EIdType: str = ''
                text: str = ''
            class PublicationTypeModel(BaseModel):
                UI: str
                text: str
            class AbstractTextModel(BaseModel):
                Label: str = ''
                NlmCategory: str = ''
                text: str
            Journal: JournalModel
            ArticleTitle: str
            Pagination: str = ''
            ELocationID: list[ELocationIDModel] = []
            AbstractText: list[AbstractTextModel] = []
            CopyrightInformation: str = ''
            AuthorList: list[AuthorModel] = []
            PublicationTypeList: list[PublicationTypeModel]
        class MedlineJournalInfoModel(BaseModel):
            MedlineTA: str
            NlmUniqueID: str
            Country: str = ''
            ISSNLinking: str = ''
        class MeshHeadingModel(BaseModel):
            UI: str = ''
            text: str = ''
        class KeywordModel(BaseModel):
            text: str = ''
        class CommentsCorrectionsModel(BaseModel):
            RefType: str = ''
            RefSource: str = ''
            PMID: str
        class ChemicalModel(BaseModel):
            class NameOfSubstanceModel(BaseModel):
                UI: str
                text: str
            RegistryNumber: str
            NameOfSubstance: NameOfSubstanceModel
        PMID: int
        DateRevised: DateRevisedModel
        Article: ArticleModel
        MedlineJournalInfo: MedlineJournalInfoModel
        MeshHeadingList: list[MeshHeadingModel] = []
        KeywordList: list[KeywordModel] = []
        CommentsCorrectionsList: list[CommentsCorrectionsModel] = []
        ChemicalList: list[ChemicalModel] = []
    class PubmedDataModel(BaseModel):
        class PubMedPubDateModel(BaseModel):
            Year: str
            Month: str
            Day: str
            Hour: str
            Minute: str
            PubStatus: str = ''
        class ArticleIdModel(BaseModel):
            IdType: str
            text: str
        class ReferenceModel(BaseModel):
            class ArticleIdModel(BaseModel):
                IdType: str
                text: str
            Citation: str
            ArticleIdList: list[ArticleIdModel]
        History: list[PubMedPubDateModel]
        ArticleIdList: list[ArticleIdModel]
        ReferenceList: list[ReferenceModel] = []
    MedlineCitation: MedlineCitationModel
    PubmedData: PubmedDataModel
    DateEntrez: str

    @property
    def PMCID(self, default: str = ''):
        for articleID in self.PubmedData.ArticleIdList:
            if articleID.IdType == 'pmc':
                return articleID.text
        return default
    
    @property
    def DOI(self, default: str = ''):
        for articleID in self.PubmedData.ArticleIdList:
            if articleID.IdType == 'doi':
                return articleID.text
        return default
    
    @property
    def Categories(self):
        return " ".join([pubType.text for pubType in self.MedlineCitation.Article.PublicationTypeList])
    
    @property
    def Abstract(self):
        return "\n".join([it.text for it in self.MedlineCitation.Article.AbstractText])

    def dataframe_dict_1d(self):
        __list__Author_fullname = []
        __list__Author_initials = []
        __list__Glossary = []
        __list__Affilations = []
        __list__Refids = []
        __list__References = []
        
        for author in self.MedlineCitation.Article.AuthorList:
            __list__Author_fullname.append(author.ForeName + ' ' + author.LastName)
            __list__Author_initials.append(author.LastName + ' ' + author.Initials)
            for aff in author.AffiliationInfo:
                if aff.Affiliation not in __list__Affilations:
                    __list__Affilations.append(aff.Affiliation)
        for keyword in self.MedlineCitation.KeywordList:
            __list__Glossary.append(keyword.text)
        for ref in self.PubmedData.ReferenceList:
            pmid = '0'
            for articleID in ref.ArticleIdList:
                if articleID.IdType == 'pubmed':
                    pmid = articleID.text
                    break
            if pmid != '0':
                __list__Refids.append(pmid)
            else:
                __list__References.append(ref.Citation.strip())

        return {
            "PMID": self.MedlineCitation.PMID,
            "PMCID": self.PMCID,
            "Title": self.MedlineCitation.Article.ArticleTitle,
            "Categories": self.Categories,
            "date_epub": self.DateEntrez,
            "Abstract": self.Abstract,
            "Author.initials": ", ".join(__list__Author_initials),
            "Author.fullname": ", ".join(__list__Author_fullname),
            "Affiliations": "; ".join(__list__Affilations),
            "Text_full": None,
            "Glossary": "; ".join(__list__Glossary),
            "journal.nlm": self.MedlineCitation.Article.Journal.ISOAbbreviation,
            "journal.longname": self.MedlineCitation.Article.Journal.Title,
            "journal.ISSNP": self.MedlineCitation.Article.Journal.ISSN_Print,
            "journal.ISSNE": self.MedlineCitation.Article.Journal.ISSN_Electronic,
            "DOI": self.DOI,
            "book.volume": self.MedlineCitation.Article.Journal.JournalIssue.Volume,
            "book.issue": self.MedlineCitation.Article.Journal.JournalIssue.Issue,
            "book.first_page": self.MedlineCitation.Article.Pagination,
            "book.last_page": '',
            "date.year": self.MedlineCitation.Article.Journal.JournalIssue.PubDate.Year,
            "date.month": self.MedlineCitation.Article.Journal.JournalIssue.PubDate.Month,
            "date.day": self.MedlineCitation.Article.Journal.JournalIssue.PubDate.Day,
            "Ref_ids": ",".join(__list__Refids),
            "References": "\n".join(__list__References),
        }
    
    @classmethod
    def from_source(self, source: dict, default = None):
        try:
            MedlineCitationDict = source.get('MedlineCitation')
            ArticleDict = MedlineCitationDict.get('Article')
            JournalDict = ArticleDict.get('Journal')
            JournalIssueDict = JournalDict.get('JournalIssue', {})
            PubmedDataDict = source.get('PubmedData')
            return self(
                MedlineCitation = self.MedlineCitationModel(
                    PMID = MedlineCitationDict.get('PMID'),
                    DateRevised = parse_obj_as(self.MedlineCitationModel.DateRevisedModel, MedlineCitationDict.get('DateRevised', {})),
                    Article = self.MedlineCitationModel.ArticleModel(
                        Journal = self.MedlineCitationModel.ArticleModel.JournalModel(
                            ISOAbbreviation = JournalDict.get('ISOAbbreviation'),
                            Title = JournalDict.get('Title'),
                            JournalIssue = self.MedlineCitationModel.ArticleModel.JournalModel.JournalIssueModel(
                                Volume = JournalIssueDict.get('Volume', ''),
                                Issue = JournalIssueDict.get('Issue', ''),
                                PubDate = parse_obj_as(self.MedlineCitationModel.ArticleModel.JournalModel.JournalIssueModel.PubDateModel, JournalIssueDict.get('PubDate', {})),
                            ),
                            ISSN_Print = JournalDict.get('ISSN_Print'),
                            ISSN_Electronic = JournalDict.get('ISSN_Electronic'),
                        ),
                        ArticleTitle = ArticleDict.get('ArticleTitle'),
                        Pagination = ArticleDict.get('Pagination', ''),
                        ELocationID = parse_obj_as(list[self.MedlineCitationModel.ArticleModel.ELocationIDModel], ArticleDict.get('ELocationID', [])),
                        AbstractText = parse_obj_as(list[self.MedlineCitationModel.ArticleModel.AbstractTextModel], ArticleDict.get('AbstractText', [])),
                        CopyrightInformation = ArticleDict.get('CopyrightInformation', ''),
                        AuthorList = parse_obj_as(list[self.MedlineCitationModel.ArticleModel.AuthorModel], ArticleDict.get('AuthorList', [])),
                        PublicationTypeList = parse_obj_as(list[self.MedlineCitationModel.ArticleModel.PublicationTypeModel], ArticleDict.get('PublicationTypeList', [])),
                    ),
                    MedlineJournalInfo = parse_obj_as(self.MedlineCitationModel.MedlineJournalInfoModel, MedlineCitationDict.get('MedlineJournalInfo')),
                    MeshHeadingList = parse_obj_as(list[self.MedlineCitationModel.MeshHeadingModel], MedlineCitationDict.get('MeshHeadingList', [])),
                    KeywordList = parse_obj_as(list[self.MedlineCitationModel.KeywordModel], MedlineCitationDict.get('KeywordList', [])),
                    CommentsCorrectionsList = parse_obj_as(list[self.MedlineCitationModel.CommentsCorrectionsModel], MedlineCitationDict.get('CommentsCorrectionsList', [])),
                    ChemicalList = parse_obj_as(list[self.MedlineCitationModel.ChemicalModel], MedlineCitationDict.get('ChemicalList', [])),
                ),
                PubmedData = self.PubmedDataModel(
                    History = parse_obj_as(list[self.PubmedDataModel.PubMedPubDateModel], PubmedDataDict.get('History')),
                    ArticleIdList = parse_obj_as(list[self.PubmedDataModel.ArticleIdModel], PubmedDataDict.get('ArticleIdList')),
                    ReferenceList = parse_obj_as(list[self.PubmedDataModel.ReferenceModel], PubmedDataDict.get('ReferenceList', [])),
                ),
                DateEntrez = source.get('DateEntrez')
            )
        except Exception:
            return default
class Article():
    def __init__(self):
        self.journal = None
        self.volume = None
        self.year = None
        self.issue = None
        self.title = None
        self.authors = None
        self.fileName = None
        self.url = None
        self.doi = None
        self.illegalTitleChars = None
        self.illegalAuthorsChars = None
        self.downloadFlag = None # MATCH FOUND, MATCH NOT FOUND, DOWNLOAD
    
    def __repr__(self):
        return self.fileName
    
    def asdict(self):
        return {
        'Journal': self.journal,
        'Volume': self.volume,
        'Year': self.year,
        'Issue': self.issue,
        'Title': self.title,
        'Authors': self.authors,
        'FileName': self.fileName,
        'URL': self.url,
        'DOI': self.doi,
        'IllegalTitleChars': self.illegalTitleChars,
        'IllegalAuthorsChars': self.illegalAuthorsChars,
        'DownloadFlag': self.downloadFlag  
        }

    __str__=__repr__


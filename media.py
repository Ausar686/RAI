class BaseMedia:
    """
    Base class for media files (i.e. audio/video).
    """
    
    def __init__(self):
        pass
    
    def __repr__(self):
        pass
    
    def __str__(self):
        pass


class VideoFile(BaseMedia):
    """
    Class for video integration into chats.
    """
    
    def __init__(self):
        super().__init__()


class AudioFile(BaseMedia):
    """
    Class for audio integration into chats.
    """
    
    def __init__(self):
        super().__init__()


class ImageFile(BaseMedia):
    """
    Class for image integration into chats.
    """
    
    def __init__(self):
        super().__init__()


class Document(BaseMedia):
    """
    Class for document (pdf/docx/zip/...) integration into chats.
    """
    
    def __init__(self):
        super().__init__()
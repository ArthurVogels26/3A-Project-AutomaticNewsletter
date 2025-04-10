from langchain.schema import Document
from typing import Optional, Dict


class ExtractedData:
    def __init__(self, source_type: str, identifier: str, title: Optional[str] = None, content:  Optional[str]= None ,  metadata: Optional[Dict] = None):
        self.source_type = source_type  
        self.identifier = identifier    
        self.title = title              
        self.content = content      
        self.metadata = metadata 

    def to_langchain_document(self):
        doc_metadata = {
            "title": self.title,
            "identifier": self.identifier,
            "source_type": self.source_type,
            **self.metadata
        }
        return Document(page_content=self.content, metadata=doc_metadata)

    def to_dict(self):
        """Retourner l'objet sous forme de dictionnaire."""
        return {
            'source_type': self.source_type,
            'identifier': self.identifier,
            'title': self.title,
            'content': self.content,
            'metadata': self.metadata
        }
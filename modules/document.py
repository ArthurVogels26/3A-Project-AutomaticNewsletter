import os
from enum import Enum


class DocType(Enum):
    PAPER = 1
    MODEL = 2
    DATASET = 3
    METHOD = 4
    UNDEFINED = 5

class Document:
    def __init__(self, link = []):
        self.link_ = link
        
        def get_docType(link) -> DocType:
            if "arxiv" in link:
                return DocType.PAPER
            
            if "huggingface.co" in link:
                if "models" in link:
                    return DocType.MODEL
                if "datasets" in link:
                    return DocType.DATASET

        self.type_ = get_docType(self.link_)

    def add_link(self,link) -> None:
        self.link_.append(link)

    def get_link(self) -> str:
        return self.link_
    
    def get_type(self) -> DocType:
        return self.type_
    
if __name__ == "__main__":
    
    link = "https://arxiv.org/pdf/1611.07004"
    doc = Document(link)
    print(doc.get_type())
    
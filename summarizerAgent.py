from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import Document
import io
import requests
from pypdf import PdfReader

def download_pdf(url):
    response = requests.get(url)
    if response.status_code == 200:
        return io.BytesIO(response.content)
    else:
        raise Exception(f"Failed to download PDF. Status code: {response.status_code}")

def extract_text_from_pdf(pdf_bytes):
    reader = PdfReader(pdf_bytes)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def create_langchain_document(text, metadata={}):
    return Document(page_content=text, metadata=metadata)

def pdf_to_langchain_document(url):
    pdf_bytes = download_pdf(url)
    text = extract_text_from_pdf(pdf_bytes)
    document = create_langchain_document(text, metadata={"source": url})
    return document


if __name__ == "__main__":

    url = "https://arxiv.org/pdf/1611.07004"
    model = OllamaLLM(model="llama3.2")
    
    print("Collecting document...\n")
    
    document = pdf_to_langchain_document(url)

    template = """
    Summarize the following text : {text}

    Your summary should follow this structure: At first, explain the context of the paper, what is it about.
    Then, make bullet points summarizing at least the different subjects: model, method, results.
    The summary should be very concise: maximum 150 words
    """

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    for token in chain.stream({"text": document.page_content}):
        print(token, end='', flush=True)
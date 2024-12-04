from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import Document
import data_extractor as d_ex


def generate_summary(data) -> str:

    model = OllamaLLM(model="llama3.2")

    template = """
    Summarize the following text: {text}

    Your summary should follow this structure: At first, explain the context of the paper, what is it about.
    Then, make bullet points summarizing at least the different subjects: model, method, results.
    The summary should be very concise: maximum 150 words
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    summary = ""
    for token in chain.stream({"text": data["content"]}):
        summary += token

    return summary


if __name__ == "__main__":

    url_or_id = "https://arxiv.org/pdf/1611.07004"
    model = OllamaLLM(model="llama3.2")
    
    print("Collecting document...\n")
    extractor= d_ex.DataExtractor()
    extracted_data = extractor.extract(url_or_id)
    document = extracted_data.to_langchain_document()

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
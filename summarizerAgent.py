from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import Document
import data_extractor as d_ex


def generate_summary(data: str) -> str:

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

def criticize_summary(data,summary: str) -> str:
    
    model = OllamaLLM(model="llama3.2")
    template = """
    You are an agent trained to criticize an AI generated summary of a text.
    The original text is here: {text}
    And the summary is here: {summary}
    Your review should be based on the following axes:
    - Conciseness: A summary is concise if the information is delivered efficiently, in a limited number of words.
    - Level of Detail: A summary has a high level of detail if it is able to explain in depth the most important aspects of the text.
    - Correctness: A summary is correct if all the information in the summary appears in the same way or in a reformulated way in the original text. It is
    incorrect if some information in the summary contradicts the original text.

    For each axis, give a grade from 1 to 10, explaining possible improvement. For the correctness. Flag every piece of info that either doesn't appear or contradicts the original text.
    At the end, give a general grade, from 1 to 10 to the summary.
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    review = ""
    for token in chain.stream({"text": data["content"], "summary": summary}):
        review += token

    return review


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
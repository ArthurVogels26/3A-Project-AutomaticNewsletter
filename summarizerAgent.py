from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import data_extractor as d_ex
import openai
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
API_KEY = os.getenv("OPENAI_API_KEY")


def classify_document(data, gpt = True) -> str:

    if gpt:
        model = ChatOpenAI(
            model="gpt-4o-mini",  # Use "gpt-4" if desired
            temperature=0.5,  # Controls the randomness of the output
            openai_api_key=API_KEY
        )
    else:
        model = OllamaLLM(model="llama3.2")

    template = """
    You are given this document: {text}

    Classify the document between these different classes: Model, Method, Dataset, Library, Tips and Tricks, Pedagogy.

    Here is a description of the different classes:

    - Model: You will classify a document as Model if the document present a machine learning model or a new neural network architecture. 
    - Method: You will classify a document as Method if it present a way of doing a specific thing, such as an evaluation method, a training method or any other process.
    - Dataset: You will classify a document as Dataset if the document present a Dataset, a collection of data.
    - Library: You will classify a document as a Library if the document present a new library, or module in any programming language. A repository containing a collection of code that can be used to perform a task can be seen as a Library too. 
    - Tips and Tricks: You will classify as Tips and Tricks a document that presents tips about something, tips and tricks are lighter than a whole method.
    - Pedagogy: You will classify as Pedagogy a document that compile information from different source on a subject in order to give pedagogical overview of the concept. A survey on different deep learning approaches to solve a problem, a collection of ressources on a thematic or a course on Deep Learning should be considered as Pedagogy.

    Your answer should only contain the class and nothing else.

    Exemple:
    Question: What is the class of this document?
    Answer: Method
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    summary = chain.invoke({"text": data["content"]})

    if hasattr(summary,'content'):
        return summary.content, (summary.usage_metadata["input_tokens"],summary.usage_metadata["output_tokens"])
    
    return summary, (0,0)


def generate_summary(data: str, gpt = True) -> str:

    if gpt:
        model = ChatOpenAI(
            model="gpt-4o-mini",  # Use "gpt-4" if desired
            temperature=0.5,  # Controls the randomness of the output
            openai_api_key=API_KEY
        )
    else:
        model = OllamaLLM(model="llama3.2")

    template = """
    Summarize the following text: {text}

    Your summary should follow this structure: At first, explain the context of the document, what the document is about.
    Then, make bullet points summarizing the principal topics of the document. It could be about the model used, the method used, the results or other topics you consider relevent.
    The summary should be very concise: maximum 150 words
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    summary = chain.invoke({"text": data["content"]})

    if hasattr(summary,'content'):
        return summary.content, (summary.usage_metadata["input_tokens"],summary.usage_metadata["output_tokens"])
    
    return summary, (0,0)

def criticize_summary(data,summary: str, gpt=True) -> str:
    
    if gpt:
        model = ChatOpenAI(
            model="gpt-4o-mini",  # Use "gpt-4" if desired
            temperature=0.5,  # Controls the randomness of the output
            openai_api_key=API_KEY
        )
    else:
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

    review = chain.invoke({"text": data["content"], "summary": summary})

    if hasattr(review,'content'):
        return review.content
    
    return review

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import openai
import os

#Safely getting the OPENAI_API_KEY
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
API_FILE = os.path.join(parent_dir,"APIKEY")
with open(API_FILE, 'r') as file:
    API_KEY = file.read()

#Creating the model
chat_model = ChatOpenAI(
    model="gpt-3.5-turbo",  # Use "gpt-4" if desired
    temperature=0.5,  # Controls the randomness of the output
    max_tokens=150,
    openai_api_key=API_KEY
)

response = chat_model.invoke("What is the capital of France?")
print(response.content)


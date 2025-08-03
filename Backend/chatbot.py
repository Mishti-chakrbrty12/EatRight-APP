import os
import cohere
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

co = cohere.Client(COHERE_API_KEY)

def ask_nutribot(question: str) -> str:
    response = co.chat(
        model="command-r-plus",
        message=question,
        temperature=0.6
    )
    return response.text

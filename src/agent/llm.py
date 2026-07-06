import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()

# Grading & rewriting: many short calls
llm_fast = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=3)

# Final answer generation: bigger Groq model, 1000 req/day free
llm_main = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, max_retries=3)

# Vision (figure transcription only, rare calls): stays on Gemini's small quota
llm_vision = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, max_retries=3)
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pinecone import Pinecone, ServerlessSpec
from rag import generate_answer, process_query, isSimilarQuery
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],  # Allow all headers
)

PC_API_KEY = os.getenv('PC_API_KEY')
PC_DUPLICATE_API_KEY = os.getenv('PC_DUPLICATE_API_KEY')
QUERY_PC_API_KEY = os.getenv('QUERY_PC_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Pinecone
pc = Pinecone(api_key=PC_API_KEY)
pc_duplicate = Pinecone(api_key=PC_DUPLICATE_API_KEY)
query_pc = Pinecone(api_key=QUERY_PC_API_KEY)
index_name = "legaltextcasesummary"

# Define Pydantic model for incoming query request
class QueryRequest(BaseModel):
    query: str

class QnARequest(BaseModel):
    query: str
    document_text: str 

@app.post("/retrieve")
async def ask_model(request: QueryRequest):
    print(f"Query for retrieval: {request.query}")
    result = isSimilarQuery(request.query)
    return {"response": result}

@app.post("/qna")
async def ask_qna_model(request: QnARequest):
    print(f"QnA Question: {request.query}")
    response = process_query(request.query)
    print(f"\nGenerated Answer: {response['answer']}")
    return {"response": response["answer"]}
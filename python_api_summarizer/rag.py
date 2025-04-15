from fastapi import FastAPI
from groq import Groq
from fastapi import HTTPException, WebSocketException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pinecone import Pinecone, ServerlessSpec
import os
import random
from dotenv import load_dotenv
import time
import re

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],  # Allow all headers
)

PC_API_KEY = os.getenv("PC_API_KEY")
PC_DUPLICATE_API_KEY = os.getenv("PC_DUPLICATE_API_KEY")
QUERY_PC_API_KEY = os.getenv("QUERY_PC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Pinecone
pc = Pinecone(api_key=PC_API_KEY)
pc_duplicate = Pinecone(api_key=PC_DUPLICATE_API_KEY)
query_pc = Pinecone(api_key=QUERY_PC_API_KEY)
index_name = "legaltextcasesummary"

# Set up Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

def isSimilarQuery(query):
    try:
        q_index_name = "legaltextcasequery"

        if q_index_name not in query_pc.list_indexes().names():
            pc_duplicate.create_index(
                name=q_index_name,
                dimension=1024,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )

        query_embedding = pc_duplicate.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={
                "input_type": "query"
            }
        )

        query_vector = query_embedding[0].values

        # Check if the query was already asked before
        q_results = query_pc.Index(q_index_name).query(
            namespace="q_ind",
            vector=query_vector,
            top_k=3,
            include_values=False,
            include_metadata=True 
        )

        if q_results['matches'] and q_results['matches'][0]['score'] >= 0.8:
            print('Query Present in q_ind')
            return q_results['matches'][0]['metadata']['text']

        # If not found, search all legal document namespaces
        best_match = None
        best_score = -1.0
        best_namespace = None

        legal_index = pc.Index(index_name)

        top_k = 3
        for i in range(1, 42):
            namespace = f"ind_{i}"
            try:
                results = legal_index.query(
                    namespace=namespace,
                    vector=query_vector,
                    top_k=top_k,
                    include_values=False,
                    include_metadata=True
                )

                for match in results['matches']:
                    if match and match['score'] > best_score:
                        best_score = match['score']
                        best_match = match
                        best_namespace = namespace

            except Exception as ns_err:
                print(f"Error querying namespace {namespace}: {ns_err}")


        if best_match:
            # Add the query to the q_ind namespace for future lookup
            best_match['metadata']['query'] = query
            query_pc.Index(q_index_name).upsert(
                vectors=[{
                    "id": best_match['id'],
                    "values": query_vector,
                    "metadata": best_match['metadata']
                }],
                namespace="q_ind"
            )
            print(f'Query Upserted from {best_namespace} with score {best_score:.3f}')
            return best_match['metadata']['text']

        return "No relevant information found in any namespace."

    except Exception as e:
        print(f"Error in isSimilarQuery: {e}")
        raise HTTPException(status_code=500, detail="Error processing query")

def generate_answer(query, retrieved_contexts):
    # Extract the text content from retrieved documents
    contexts = []
    retrieved_dict = {}
    # Convert the Pinecone object to a dict for easier handling
    if isinstance(retrieved_contexts, str):
        contexts = [retrieved_contexts]
    elif isinstance(retrieved_contexts, dict):
        retrieved_dict = retrieved_contexts
        if 'matches' in retrieved_dict:
            for match in retrieved_dict['matches']:
                if 'metadata' in match and 'text' in match['metadata']:
                    text = match['metadata']['text']
                    if text:
                        contexts.append(text)
    else:
        try:
            retrieved_dict = retrieved_contexts.to_dict()
            if 'matches' in retrieved_dict:
                for match in retrieved_dict['matches']:
                    if 'metadata' in match and 'text' in match['metadata']:
                        text = match['metadata']['text']
                        if text:
                            contexts.append(text)
        except Exception as e:
            print(f"Error extracting context: {e}")

    
    # Extract text from matches
    if 'matches' in retrieved_dict:
        for match in retrieved_dict['matches']:
            if 'metadata' in match and 'text' in match['metadata']:
                # In a real scenario this would contain the actual text
                text = match['metadata']['text']
                if text:  # Only add non-empty text
                    contexts.append(text)
    
    context_text = "\n\n".join(contexts)
    prompt = f"""
You are a helpful assistant specialized in Indian tax law. Use ONLY the following context to answer the question. 
If you don't have enough information to answer this question, say "I don't have enough information to answer this question."

Context:
{context_text}

Question: {query}

Answer:
"""
    
    # Generate answer using Groq's LLama model
    try:
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based only on the provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"

def process_query(query):
    # Add debugging information
    print("Retrieving similar documents...")
    retrieved_results = isSimilarQuery(query)

    print(f"Type of retrieved_results: {type(retrieved_results)}")
    
    print("Generating answer...")
    answer = generate_answer(query, retrieved_results)
    
    return {
        "query": query,
        "retrieved_contexts": retrieved_results,
        "answer": answer
    }

def process_newdata_query(query,document_text):
    chunks = chunk_text(document_text)
    namespace,success = upsert_new_chunked_text(chunks)
    print(success)
    if success:
        print("Retrieving similar documents...")
        retrieved_results = retrieve_when_doc_given(namespace,query)
        print(f"Type of retrieved_results: {type(retrieved_results)}")
        
        print("Generating answer...")
        answer = generate_answer(query, retrieved_results)
        
        return {
            "query": query,
            "retrieved_contexts": retrieved_results,
            "answer": answer
        }
    else:
        return {
            "query": query,
            "answer":"Failed to upsert documents please try again"
        }

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
nltk.download("punkt_tab")  # Download NLTK tokenizer model

def chunk_text(text, max_tokens=505):
    """Splits text into chunks of max 505 tokens while keeping sentence structure intact."""
    sentences = sent_tokenize(text)  # Split into sentences
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        words = word_tokenize(sentence)  # Tokenize words
        sentence_length = len(words)

        if current_length + sentence_length > max_tokens:
            if current_chunk:
                chunks.append(" ".join(current_chunk))  # Save previous chunk
            current_chunk = words  # Start new chunk
            current_length = sentence_length
        else:
            current_chunk.extend(words)
            current_length += sentence_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))  # Add last chunk

    return chunks

def upsert_new_chunked_text(chunks):
    data = []
    for j in range(len(chunks)):
        data.append({'id':'ns_'+str(random.randint(75000,1000000))+'_'+str(j),'text':chunks[j],'summary':'NA'})

    for i in range(len(data)):
        namespace_count = 41
        try:
            datas = []
            embeddings = []
            for j in range(1,3):
                # Slice the data batch
                s = i+(j-1)*96
                if s>=len(data):
                    break
                e = min(i+j*96,len(data))
                datas.append(data[s:e])
                # Generate embeddings
                emb = pc_duplicate.inference.embed(
                    model="multilingual-e5-large",
                    inputs=[d['text'] for d in datas[j-1]],
                    parameters={"input_type": "passage", "truncate": "END"}
                )
                embeddings.append(emb) 
                time.sleep(15)

            # Prepare records for Pinecone
            records = []
            for j in range(len(datas)):
                for d, e in zip(datas[j], embeddings[j]):
                    try:
                        # # Truncate text if metadata exceeds the limit
                        truncated_text = d['text']
                        summary_text = d['summary']
                        
                        # Add the record
                        records.append({
                            "id": d['id'],
                            "values": e['values'],
                            "metadata": {"text": truncated_text,'summary':summary_text}
                        })
                    except Exception as inner_error:
                        print(f"Error processing record ID {d['id']}: {inner_error}")
                
            # Upsert records into the Pinecone index
            pinecone_index = pc.Index(index_name)
            pinecone_index.upsert(
                vectors=records,
                namespace=f"ind_{namespace_count}"
            )
            return namespace_count,True
        except Exception as batch_error:
            print(f"Error processing batch {i}: {batch_error}")
            return namespace_count,False

def retrieve_when_doc_given(namespace,query):
    # when a file is uploaded then other type of retrieval
    try:
        query_embedding = pc_duplicate.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={
                "input_type": "query"
            }
        )

        query_vector = query_embedding[0].values

        # If not found, search all legal document namespaces
        best_match = None
        best_score = -1.0
        best_namespace = None

        legal_index = pc.Index(index_name)

        top_k = 3
        try:
            results = legal_index.query(
                namespace=f"ind_{namespace}",
                vector=query_vector,
                top_k=top_k,
                include_values=False,
                include_metadata=True
            )

            for match in results['matches']:
                if match and match['score'] > best_score:
                    best_score = match['score']
                    best_match = match
                    best_namespace = namespace

        except Exception as ns_err:
            print(f"Error querying namespace {namespace}: {ns_err}")


        if best_match:
            # Add the query to the q_ind namespace for future lookup
            best_match['metadata']['query'] = query
            return best_match['metadata']['text']

        return "No relevant information found in any namespace."

    except Exception as e:
        print(f"Error in isSimilarQuery: {e}")
        raise HTTPException(status_code=500, detail="Error processing query")

def clean_text(text: str) -> str:
    # Replace any character that's not a letter, digit, or whitespace with a space.
    cleaned = re.sub(r'[^A-Za-z0-9\s]', ' ', text)
    # Replace one or more whitespace characters with a single space and remove leading/trailing spaces.
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned
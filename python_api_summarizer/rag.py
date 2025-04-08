from fastapi import FastAPI
from groq import Groq
from fastapi import HTTPException, WebSocketException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pinecone import Pinecone, ServerlessSpec
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
        for i in range(1, 41):
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
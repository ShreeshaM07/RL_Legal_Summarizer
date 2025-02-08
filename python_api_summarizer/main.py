from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pinecone import Pinecone, ServerlessSpec

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize Pinecone
pc = Pinecone(api_key="pcsk_7E1vP3_QK2W6M9XCiHufegYYXyYurwWGddethJCY4TYTcm15PnRKS5EDMKa11KyYvNjVbB")
pc_duplicate = Pinecone(api_key="pcsk_7VMsMN_PRA9cnkzr5tpG92dfxqxcAhhczX6RwifiDqkCTa4ruyWZX5AXyJNgiCezztAgvT")
query_pc = Pinecone(api_key="pcsk_6zNLd7_Lep8rBqzNatyGXGykxBumtiAcYE493jHtrgTkjhuJYdDBGeByH8KXAFYVdXLjrq")
index_name = "legaltextcasesummary"

def isSimilarQuery(query):
    # Create a Pinecone index
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
        # Convert the query into a numerical vector that Pinecone can search with
        query_embedding = pc_duplicate.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={
                "input_type": "query"
            }
        )
        q_results = query_pc.Index(q_index_name).query(
            namespace="q_ind",
            vector=query_embedding[0].values,
            top_k=3,
            include_values=False,
            include_metadata=True 
        )
        q_records=[]
        if q_results['matches'] and q_results['matches'][0]['score']>=0.8:
            print('Query Present')
            return q_results['matches'][0]['metadata']['text']
        else:
            # Search the index for the three most similar vectors
            results = pc.Index(index_name).query(
                namespace="ind_1",
                vector=query_embedding[0].values,
                top_k=3,
                include_values=False,
                include_metadata=True
            )
            q_results= results
            for i in range(3):
                q_results['matches'][i]['metadata']['query'] = query
                q_records.append({
                    "id":q_results['matches'][i]['id'],
                    "values":query_embedding[0].values,
                    "metadata":q_results['matches'][i]['metadata'],
                })
            query_pc.Index(q_index_name).upsert(
                vectors=q_records,
                namespace="q_ind",
            )
            print('Query Upserted')
            return q_records[0]['metadata']['text']
    
    except Exception as e:
        print(f"Error in isSimilarQuery: {e}")
        raise HTTPException(status_code=500, detail="Error processing query")

# Define Pydantic model for incoming query request
class QueryRequest(BaseModel):
    query: str

# FastAPI endpoint to handle the query
@app.post("/retrieve")
async def ask_model(request: QueryRequest):
    print(request.query)
    result = isSimilarQuery(request.query)  # Call the function to process the query
    return {"response": result}
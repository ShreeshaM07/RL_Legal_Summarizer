def isSimilarQuery(query):
    # Create a Pinecone index
    q_index_name = "legaltextcasequery"
    if q_index_name not in query_pc.list_indexes().names():
        pc_duplicate.create_index(
            name=q_index_name, 
import chromadb
from chromadb.utils import embedding_functions


em_fun = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
DBclient = chromadb.PersistentClient("./my_chromaDB")

def get_ids(collection_name="code_snippet"):
    collection = DBclient.get_collection(name=collection_name, embedding_function=em_fun)

    return collection.get()['ids']

def relevent_chunks(query: str, top_k=3, collection_name="code_snippet"):
    collection = DBclient.get_collection(name=collection_name, embedding_function=em_fun)

    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    return results["documents"][0][0:top_k]

collection = DBclient.get_collection(name="code_snippet", embedding_function=em_fun)
print(collection.id)

import chromadb
from chromadb.utils import embedding_functions

em_fun = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
DBclient = chromadb.PersistentClient("./my_chromaDB")

def embed_store(chunks: list, metadatas, ids, collection_name="code_snippet"):
    collection = DBclient.get_or_create_collection(name=collection_name, embedding_function=em_fun)

    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )

    return len(chunks)



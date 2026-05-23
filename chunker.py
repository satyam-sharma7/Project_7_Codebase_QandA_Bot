

"""
Still need to handle code of other languages

"""

import ast
import time
code = """import pandas as pd
import numpy as np
a = 4
b = 0
c = a+b
def relevent_chunks(query: str, top_k=1, collection_name="my_embedded_chunks"):
    collection = DBclient.get_collection(name=collection_name,
        embedding_function=em_fun
        )
    
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    print(results["documents"][0][0:top_k])
    return results["documents"][0][0:top_k]


def lets_see(query: str, top_k=1, collection_name="my_embedded_chunks"):
    collection = DBclient.get_collection(name=collection_name,
        embedding_function=em_fun
        )
    
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    print(results["documents"][0][0:top_k])
    return results["documents"][0][0:top_k]

async def timer():
    await time.sleep(3)
"""

def chunk_python_code(source_code: str, file_name: str):
    source_lines = source_code.splitlines()
    tree = ast.parse(source_code)
    chunks = []
    metadatas = []
    ids = []
    for no, node in enumerate(tree.body):
        chunk = None
        metadata = None
        id = None

        # chunk functions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = node.end_lineno
            chunk =  "\n".join(source_lines[start-1:end]),
            metadata = {
                "file_name":file_name,
                "type":"function",
                "name":node.name,
                "start_line":start,
                "end_line":end
            }
            id = f"{file_name}__{node.name}__{no}"
        
        # chunk classes
        elif isinstance(node, (ast.ClassDef)):
            start = node.lineno
            end = node.end_lineno
            chunk =  "\n".join(source_lines[start-1:end]),
            metadata = {
                "file_name":file_name,
                "type":"class",
                "name":node.name,
                "start_line":start,
                "end_line":end
            }
            id = f"{file_name}__{node.name}__{no}"

        # Chunk Top-Level Code (Imports, global variables, scripts)
        else:
            start = node.lineno
            end = node.end_lineno
            chunk =  "\n".join(source_lines[start-1:end]),
            metadata = {
                "file_name":file_name,
                "type":"top_level",
                "name":f"{file_name}_top_level",
                "start_line":start,
                "end_line":end
            }
            id = f"{file_name}_top_level__{no}"

        if chunk:
            chunks.append(chunk[0])
            metadatas.append(metadata)
            ids.append(id)

    return chunks, metadatas, ids


chunks, metadatas, ids = chunk_python_code(code, "retrieve.py")
print("Chunked sussesfully")

from chunk_store import embed_store

count = embed_store(chunks, metadatas, ids)
print(count)




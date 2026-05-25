

"""
Still need to handle code of other languages

"""

import ast
import time

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

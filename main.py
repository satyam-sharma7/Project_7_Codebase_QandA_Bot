import argparse
import subprocess
import pathlib
import shutil
import stat
import os
from openai import OpenAI
import tomllib
import questionary
from dotenv import load_dotenv

from chunker import chunk_python_code
from chunk_store import embed_store
from chunk_retrieve import get_ids, relevent_chunks

parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(dest="command")

ingest_parser = subparser.add_parser("ingest")
ingest_parser.add_argument("--repo", required=True)

query_parser = subparser.add_parser("query")
query_parser.add_argument("question")        # position argument

args = parser.parse_args()

load_dotenv()

with open("config.toml", 'rb') as f:
    config = tomllib.load(f)

MODEL = questionary.select(
    "Select LLM Model",
    choices=["Gemini", "Qwen", "Minmax", "GLM"]
).ask()

MODEL = config["models"][MODEL.lower()]

client = OpenAI(
    base_url=MODEL['url'],
    api_key= os.getenv(MODEL["api"])
)

def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def repo_handler(repo:str):
    cloned_dir ="./repos/" + repo.split("/")[-1].split(".")[0]
    clone_repo = subprocess.run(['git', 'clone', repo, f'{cloned_dir}'], text=True, capture_output=True)

    # print("STDERR:", clone_repo.stderr)

    if clone_repo.returncode == 0:
        print("Repo Sucessfully cloned.")

        total_files = 0
        total_chunks = 0
        for path in pathlib.Path("./repos").rglob("*.py"):
            code = path.read_text()

            chunks, metadatas, ids = chunk_python_code(code, path.name)

            chunks_count = embed_store(chunks, metadatas, ids)

            total_files += 1
            total_chunks += chunks_count        
        
        print(f"Found {total_files} Python files, {total_chunks} chunks")

        shutil.rmtree(cloned_dir, onexc=remove_readonly)
        print("Cloned Repo Deleted.")


    elif clone_repo.returncode != 0:
        print("Check Repo url.")



def query_handler(query:str):
    chunks_ids = get_ids()

    chunks = relevent_chunks(query)
    print("Retrieved chunks")
    for chu in chunks:
        print(chu[:50])

    PROMPT = f"""
    You are a helpful codebase explainer 
    who helps to expalin user query about codebase and
    give suggestion to improve codebase if user asked you
    to.
    """

    response = client.chat.completions.create(
        model=MODEL['name'],
        messages=[
            {"role":"system", "content": PROMPT},

            {
                "role":"user",
                "content":
                f"""
                here is user query:
                "{query}". 
                Here is the the relevent retrived code:
                "{chunks[0]}\n\n{chunks[1]}\n\n{chunks[2]}"
                """
            }
        ],
        stream=True
    )

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)




if args.command == "ingest":
    repo_handler(args.repo)
elif args.command == "query":
    query_handler(args.question)





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
import json
from rich.console import Console
from rich.panel import Panel

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
console = Console()

with open("config.toml", 'rb') as f:
    config = tomllib.load(f)

print("\n")
console.print(
    Panel(
        "Please choose the underlying LLM engine.",
        title="[bold green]Configuration Studio[/bold green]",
        expand=False,
    )
)
MODEL = questionary.select(
    message= "Select LLM Model",
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
        console.print("[green]Repo Sucessfully cloned.[/]\n")

        total_files = 0
        total_chunks = 0
        for path in pathlib.Path("./repos").rglob("*.py"):
            code = path.read_text()

            chunks, metadatas, ids = chunk_python_code(code, path.name)

            chunks_count = embed_store(chunks, metadatas, ids)

            total_files += 1
            total_chunks += chunks_count        
        
        console.print(f"[blue]Found {total_files} Python files, {total_chunks} chunks[blue]\n")

        shutil.rmtree(cloned_dir, onexc=remove_readonly)
        console.print("[red]Cloned Repo Deleted.[/]\n")


    elif clone_repo.returncode != 0:
        console.print("[yellow]Please Check Repo url.[/]\n")

def chunk_eval(query:str, chunks:list, ids:list) -> float:
    PROMPT = """
    You are provided with user QUERY
    CHUNKS(chuks will be used to answer user's query) and
    IDS(IDs of all chunks contained in dataset id represents Filename_FunctioNname_ChunkNo).
    Your work is to evaluate chuks relevency to answering the
    question you have to give score between 0 to 1.
    Provide answer in following format.
    EXAMPLE:
    {
        "score": 0.73
    }
    """
    
    response = client.chat.completions.create(
        model=MODEL['name'],
        messages=[
            {"role":"system", "content":PROMPT},
            {
            "role":"user", "content":
            f"QUERY:{query}\n\nCHUNKS:{chunks}\n\nids:{ids}"
            }
        ],
        response_format={"type":"json_object"}
    )

    score = json.loads(response.choices[0].message.content)['score']
    console.print(f"[blue]Chunk Score: {score}[/]\n")
    return score

def query_generator(query:str, ids:str, loop_count:int):
        
    PROMPT = """
    You are provided with user QUERY and
    IDS(IDs of all chunks contained in dataset id represents Filename_FunctioNname_ChunkNo).
    Using ids(Assume function).
    since you know the functions name of code database understand user's requirement
    and generate query that aligns with user's "query" and retrieve more relevent chunks
    of your query.
    Provide content in following formate:
    {
        "new_query": "your generate query will be here."
    }
    """

    response = client.chat.completions.create(
        model=MODEL['name'],
        messages=[
            {"role":"system", "content":PROMPT},
            {
            "role":"user", "content":
            f"QUERY:{query}\n\nids:{ids}"
            }
        ],
        response_format={"type":"json_object"}
    )

    new_query =  json.loads(response.choices[0].message.content)['new_query']
    loop_count += 1
    console.print(f"[bold]New generated qury: {new_query}[/]\n")
    query_handler(new_query, loop_count)


    

def query_handler(query:str, loop_count=0):
    chunks_ids = get_ids()

    chunks = relevent_chunks(query)
    console.print("[green]Retrieved chunks Preview:[/]")
    for chu in chunks:
        print(" "*5 +chu[:50])
    print("\n")

    chunk_score = chunk_eval(query, chunks, chunks_ids)

    if chunk_score >= 0.60 and loop_count<2:
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

        print("\033[92mBot: !\033[0m", end="")
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="", flush=True)

    elif chunk_score < 0.60 and loop_count<2:
        query_generator(query, chunks_ids, loop_count)

    elif loop_count>=2:
        console.print("[bold][red]Max try exceed.[/bold][/red]")

if args.command == "ingest":
    repo_handler(args.repo)
elif args.command == "query":
    query_handler(args.question)





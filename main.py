import argparse
import subprocess
import pathlib
import shutil

from chunker import chunk_python_code
from chunk_store import embed_store



parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(dest="command")

ingest_parser = subparser.add_parser("ingest")
ingest_parser.add_argument("--repo", required=True)

query_parser = subparser.add_parser("query")
query_parser.add_argument("question")        # position argument

args = parser.parse_args()


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

        shutil.rmtree('./repo')
        
        
        print(f"Found {total_files} Python files, {total_chunks} chunks")




    elif clone_repo.returncode != 0:
        print("Check Repo url.")




if args.command == "ingest":
    repo_handler(args.repo)
elif args.command == "query":
    print(args.question)

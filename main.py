import argparse


parser = argparse.ArgumentParser()
subparser = parser.add_subparsers(dest="command")

ingest_parser = subparser.add_parser("ingest")
ingest_parser.add_argument("--docs", required=True)

query_parser = subparser.add_parser("query")
query_parser.add_argument("question")        # position argument


args = parser.parse_args()


if args.command == "ingest":
    print(args.docs)
elif args.command == "query":
    print(args.question)

import logging
import argparse
from config import MAX_PAGES, DATABASE_URL
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from crawler.engine import run
from crawler.seed import load_seeds
from analysis.stats import show_stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)

parser = argparse.ArgumentParser(description='crauler')
subparser = parser.add_subparsers(dest='command')

seed_parser = subparser.add_parser('seed', help="Load seed URLs into frontier")
crawl_parser = subparser.add_parser('crawl', help="Run the crawler")
stats_parser = subparser.add_parser('stats', help="Show crawl statistics")
crawl_parser.add_argument("--max-pages", type=int, default=MAX_PAGES, help=f"Maximum pages to fetch (default: {MAX_PAGES})")

args = parser.parse_args()

engine = create_engine(DATABASE_URL)
if args.command == "seed":
    with Session(engine) as session:
        count = load_seeds(session)
        print(f"Seeds added: {count}")
elif args.command == "crawl":
    run(max_pages=args.max_pages)
elif args.command == "stats":
    with Session(engine) as session:
        show_stats(session)
else:
    parser.print_help()

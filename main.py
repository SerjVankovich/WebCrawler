import asyncio
import os
import argparse
from src.crawler.async_crawler import AsyncCrawler
from src.db.db_saver import DBSaver


def parse_args():
    parser = argparse.ArgumentParser(description='Web Crawler')
    parser.add_argument('--url', type=str, default="https://spbu.ru",
                        help='Starting URL for crawling')
    parser.add_argument('--max-pages', type=int, default=50,
                        help='Maximum number of pages to crawl')
    parser.add_argument('--concurrency', type=int, default=30,
                        help='Number of concurrent tasks')
    return parser.parse_args()


async def main():
    args = parse_args()
    db_url = os.getenv("DATABASE_URL")

    crawler = AsyncCrawler(
        args.url, max_pages=args.max_pages, concurrency=args.concurrency)
    await crawler.crawl()
    crawler.report()

    db_saver = DBSaver(db_url=db_url)
    db_saver.save_to_db(crawler.get_internalLinks(),
                        crawler.get_externalDomains())
    db_saver.close()

    crawler.save_links()


if __name__ == "__main__":
    asyncio.run(main())

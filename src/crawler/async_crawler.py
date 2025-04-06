import asyncio
import random
import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from tqdm.asyncio import tqdm


class AsyncCrawler:
    def __init__(self, base_url, max_pages=100, concurrency=10):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.concurrency = concurrency

        self.visited = set()
        self.to_visit = asyncio.Queue()
        self.to_visit.put_nowait(base_url)
        self.lock = asyncio.Lock()  # 🔒

        self.total_links = 0
        self.internal_links = {}
        self.external_links = {}
        self.broken_pages = {}
        self.unique_resources = set()

        # Логирование в файл
        logging.basicConfig(
            filename="crawler.log",
            filemode='w',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.logger = logging.getLogger("crawler")

    def is_internal(self, url):
        netloc = urlparse(url).netloc
        return netloc == "" or netloc == self.domain

    def random_user_agent(self):
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X)",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B)",
        ]
        return random.choice(agents)

    async def fetch(self, session: ClientSession, url: str):
        try:
            # 🤫 Sleep to be polite
            # await asyncio.sleep(random.uniform(0.5, 1.5))

            headers = {
                "User-Agent": self.random_user_agent()
            }
            async with session.get(url, timeout=10, headers=headers) as response:
                status = response.status
                if status != 200:
                    async with self.lock:
                        self.broken_pages[url] = status
                    self.logger.warning(f"Broken link ({status}): {url}")
                    return None
                self.logger.info(f"Fetched ({status}): {url}")
                return await response.text()
        except Exception as e:
            async with self.lock:
                self.broken_pages[url] = str(e)
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def is_valid_link(self, url):
        """Проверка на валидность ссылки (не mailto, tel и т.д.)"""
        invalid_schemes = ['mailto:', 'tel:', 'javascript:']
        return not any(url.lower().startswith(scheme) for scheme in invalid_schemes)

    async def handle_url(self, session: ClientSession, progress):
        while not self.to_visit.empty():
            url = await self.to_visit.get()

            async with self.lock:
                if url in self.visited or len(self.visited) >= self.max_pages:
                    continue
                self.visited.add(url)
                self.unique_resources.add(url)
                progress.update(1)

            html = await self.fetch(session, url)
            if not html:
                continue

            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup.find_all('a', href=True):
                href = tag['href'].split('#')[0].rstrip('/')
                if not self.is_valid_link(href):
                    continue

                full_url = urljoin(url, href)
                async with self.lock:
                    self.total_links += 1
                    self.unique_resources.add(full_url)

                    if self.is_internal(full_url):
                        if full_url not in self.internal_links:
                            self.internal_links[full_url] = 0
                        self.internal_links[full_url] += 1
                        if full_url not in self.visited:
                            await self.to_visit.put(full_url)
                    else:
                        if full_url not in self.external_links:
                            self.external_links[full_url] = 0
                        self.external_links[full_url] += 1

    async def crawl(self):
        async with aiohttp.ClientSession() as session:
            with tqdm(total=self.max_pages, desc="Crawling pages") as progress:
                tasks = [self.handle_url(session, progress)
                         for _ in range(self.concurrency)]
                await asyncio.gather(*tasks)

    def save_links(self):
        """Сохранение всех внутренних ссылок и внешних доменов"""
        # Сохраняем внутренние ссылки в файл
        with open('internal_links.txt', 'w') as file:
            for link, count in self.internal_links.items():
                file.write(f"{link} - {count}\n")
        self.logger.info(
            f"Saved {len(self.internal_links)} internal links to internal_links.txt")

        external_resources = {}
        for link, count in self.external_links.items():
            domain = urlparse(link).netloc
            if (domain not in external_resources):
                external_resources[domain] = 0
            external_resources[domain] += count

        # Сохраняем уникальные внешние домены в файл
        with open('external_domains.txt', 'w') as file:
            for domain, count in external_resources.items():
                file.write(f"{domain} - {count}\n")
        self.logger.info(
            f"Saved {len(external_resources)} external domains to external_domains.txt")

    def get_internalLinks(self):
        """Получение внутренних ссылок"""
        return self.internal_links

    def get_externalLinks(self):
        """Получение внешних ссылок"""
        return self.external_links

    def get_externalDomains(self):
        """Получение внешних доменов"""
        external_domains = {}
        for link, count in self.external_links.items():
            domain = urlparse(link).netloc
            if domain not in external_domains:
                external_domains[domain] = 0
            external_domains[domain] += count
        return external_domains

    def report(self):
        print("Общее количество страниц:", len(self.visited))
        print("Общее количество ссылок:", self.total_links)
        print("Внутренние ссылки:", len(self.internal_links))
        print("Внешние ссылки:", len(self.external_links))
        print("Неработающие страницы:", len(self.broken_pages))
        print("Уникальные ресурсы:", len(self.unique_resources))

        print("\nСписок неработающих страниц:")
        for url, reason in self.broken_pages.items():
            print(f"  {url}: {reason}")

        self.logger.info("CRAWL COMPLETE")
        self.logger.info(f"Visited: {len(self.visited)}")
        self.logger.info(f"Broken: {len(self.broken_pages)}")

import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
from src.crawler.async_crawler import AsyncCrawler
import logging

pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def crawler():
    base_url = "http://example.com"
    crawler = AsyncCrawler(base_url, max_pages=10, concurrency=2)
    return crawler


def test_initialization(crawler):
    assert crawler.base_url == "http://example.com"
    assert crawler.domain == "example.com"
    assert crawler.max_pages == 10
    assert crawler.concurrency == 2
    assert isinstance(crawler.to_visit, asyncio.Queue)
    assert crawler.to_visit.qsize() == 1  # base_url добавлен в очередь
    assert isinstance(crawler.lock, asyncio.Lock)
    assert crawler.visited == set()
    assert crawler.total_links == 0
    assert crawler.internal_links == {}
    assert crawler.external_links == {}
    assert crawler.broken_pages == {}
    assert crawler.unique_resources == set()


@pytest.mark.parametrize("url, expected", [
    ("http://example.com/page", True),
    ("http://example.com", True),
    ("https://example.com", True),  # HTTPS тоже считается внутренним
    ("/relative/path", True),       # Относительный путь
    ("http://other.com", False),
    ("https://sub.example.com", False),
])
def test_is_internal(crawler, url, expected):
    assert crawler.is_internal(url) == expected


@pytest.mark.parametrize("url, expected", [
    ("http://example.com", True),
    ("https://example.com/page", True),
    ("mailto:someone@example.com", False),
    ("tel:+1234567890", False),
    ("javascript:void(0)", False),
    ("/relative/path", True),
])
def test_is_valid_link(crawler, url, expected):
    assert crawler.is_valid_link(url) == expected


def test_random_user_agent(crawler):
    user_agent = crawler.random_user_agent()
    assert user_agent in [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X)",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B)",
    ]


@pytest.mark.asyncio
async def test_fetch_success(crawler):
    url = "http://example.com"
    mock_response_text = "<html><a href='/page1'>Link</a></html>"

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = mock_response_text

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_response

    with patch("aiohttp.ClientSession.get", return_value=mock_context_manager):
        async with aiohttp.ClientSession() as session:
            result = await crawler.fetch(session, url)
            assert result == mock_response_text
            assert url not in crawler.broken_pages


@pytest.mark.asyncio
async def test_fetch_failure(crawler):
    url = "http://example.com"

    async def mock_get(*args, **kwargs):
        raise aiohttp.ClientError("Connection failed")

    with patch.object(aiohttp.ClientSession, "get", new=mock_get):
        async with aiohttp.ClientSession() as session:
            result = await crawler.fetch(session, url)
            assert result is None
            assert url in crawler.broken_pages
            assert isinstance(crawler.broken_pages[url], str)


@pytest.mark.asyncio
async def test_handle_url(crawler):
    url = "http://example.com"
    mock_html = """
    <html>
        <a href="/page1">Internal</a>
        <a href="http://other.com">External</a>
        <a href="mailto:someone@example.com">Email</a>
    </html>
    """

    with patch.object(crawler, "fetch", AsyncMock(return_value=mock_html)):
        progress = MagicMock()
        progress.update = MagicMock()

        async with aiohttp.ClientSession() as session:
            await crawler.handle_url(session, progress)

            assert url in crawler.visited
            assert crawler.total_links >= 2  # Две валидные ссылки
            assert "http://example.com/page1" in crawler.internal_links
            assert crawler.internal_links["http://example.com/page1"] == 2
            assert "http://other.com" in crawler.external_links
            assert crawler.external_links["http://other.com"] == 2
            assert "http://example.com/page1" in crawler.unique_resources
            assert "http://other.com" in crawler.unique_resources
            assert progress.update.called


def test_save_links(crawler, caplog):
    caplog.set_level(logging.INFO)
    crawler.internal_links = {
        "http://example.com/page1": 2,
        "http://example.com/page2": 1
    }
    crawler.external_links = {
        "http://other.com": 3,
        "http://another.com/page": 1
    }

    with patch("builtins.open", new=MagicMock()):
        crawler.save_links()

    assert "Saved 2 internal links" in caplog.text
    assert "Saved 2 external domains" in caplog.text


def test_get_external_domains(crawler):
    crawler.external_links = {
        "http://other.com/page1": 2,
        "http://other.com/page2": 1,
        "http://another.com": 3
    }
    domains = crawler.get_externalDomains()
    assert domains == {
        "other.com": 3,
        "another.com": 3
    }


def test_report(crawler, capsys):
    crawler.visited = {"http://example.com", "http://example.com/page1"}
    crawler.total_links = 5
    crawler.internal_links = {"http://example.com/page1": 2}
    crawler.external_links = {"http://other.com": 1}
    crawler.broken_pages = {"http://example.com/404": "404"}
    crawler.unique_resources = {"http://example.com",
                                "http://example.com/page1", "http://other.com"}

    crawler.report()
    captured = capsys.readouterr()

    assert "Общее количество страниц: 2" in captured.out
    assert "Общее количество ссылок: 5" in captured.out
    assert "Внутренние ссылки: 1" in captured.out
    assert "Внешние ссылки: 1" in captured.out
    assert "Неработающие страницы: 1" in captured.out
    assert "Уникальные ресурсы: 3" in captured.out
    assert "http://example.com/404: 404" in captured.out

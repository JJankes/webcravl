from unittest.mock import patch

from webcravl.crawler import crawl_site


class StubResponse:
    def __init__(self, body: bytes, content_type: str, status: int = 200, charset: str = "utf-8") -> None:
        self.body = body
        self.status = status
        self.headers = {"Content-Type": f"{content_type}; charset={charset}"}

    def read(self) -> bytes:
        return self.body

    def getcode(self) -> int:
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def get(self, key: str, default=None):
        return self.headers.get(key, default)

    def get_content_charset(self):
        content_type = self.headers.get("Content-Type", "")
        if "charset=" in content_type:
            return content_type.split("charset=")[-1]
        return None


@patch("webcravl.crawler.urlopen")
def test_crawl_collects_minimum_sized_images(mock_urlopen):
    base_url = "https://example.com"
    start_page = "<html><body><img src='image.jpg'/><a href='page2'>Next</a></body></html>"
    second_page = "<html><body><img src='small.jpg'/></body></html>"

    def urlopen_side_effect(request, timeout=10):
        url = request if isinstance(request, str) else request.full_url
        if url.endswith("/robots.txt"):
            return StubResponse(b"User-agent: *\nAllow: /", "text/plain")
        if url.endswith("/image.jpg"):
            return StubResponse(b"0" * 1500, "image/jpeg")
        if url.endswith("/small.jpg"):
            return StubResponse(b"0" * 500, "image/jpeg")
        if url.endswith("/page2"):
            return StubResponse(second_page.encode(), "text/html")
        return StubResponse(start_page.encode(), "text/html")

    mock_urlopen.side_effect = urlopen_side_effect

    results = crawl_site(base_url, max_depth=1, min_size=1000)

    assert len(results) == 1
    assert results[0].url == base_url + "/image.jpg"
    assert results[0].size_bytes == 1500


@patch("webcravl.crawler.urlopen")
def test_respects_robots_rules(mock_urlopen):
    base_url = "https://example.com"
    start_page = "<html><body><img src='image.jpg'/></body></html>"

    def urlopen_side_effect(request, timeout=10):
        url = request if isinstance(request, str) else request.full_url
        if url.endswith("/robots.txt"):
            return StubResponse(b"User-agent: *\nDisallow: /", "text/plain")
        if url.endswith("/image.jpg"):
            return StubResponse(b"0" * 2000, "image/jpeg")
        return StubResponse(start_page.encode(), "text/html")

    mock_urlopen.side_effect = urlopen_side_effect

    results = crawl_site(base_url, max_depth=1, min_size=0)

    assert results == []

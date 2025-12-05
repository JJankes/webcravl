import logging
import re
from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import List, Optional, Set, Tuple
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


@dataclass
class ImageResult:
    url: str
    size_bytes: int


class RobotsHelper:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self._parser = RobotFileParser()
        self._initialized = False

    def load(self) -> None:
        robots_url = urljoin(self.base_url, "/robots.txt")
        try:
            with urlopen(robots_url, timeout=10) as response:  # type: ignore[arg-type]
                content = response.read().decode("utf-8", errors="ignore")
                self._parser.parse(content.splitlines())
        except (URLError, OSError):
            logger.debug("Robots.txt unavailable, allowing all paths")
            self._parser.parse(["User-agent: *", "Allow: /"])
        self._initialized = True

    def can_fetch(self, url: str) -> bool:
        if not self._initialized:
            self.load()
        return self._parser.can_fetch("*", url)


class LinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: Set[str] = set()
        self.images: Set[str] = set()

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_dict = dict(attrs)
        if tag == "a" and "href" in attr_dict and attr_dict["href"]:
            absolute = urljoin(self.base_url, attr_dict["href"])
            if absolute.startswith("http"):
                self.links.add(normalize_url(absolute))
        if tag == "img" and "src" in attr_dict and attr_dict["src"]:
            absolute = urljoin(self.base_url, attr_dict["src"])
            if absolute.startswith("http"):
                self.images.add(absolute)


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized_path = re.sub(r"/+$", "/", parsed.path) if parsed.path else "/"
    normalized = parsed._replace(path=normalized_path, fragment="").geturl()
    return normalized


def is_jpeg_url(url: str) -> bool:
    return url.lower().endswith((".jpg", ".jpeg"))


def fetch_page(url: str) -> Optional[str]:
    try:
        with urlopen(url, timeout=10) as response:  # type: ignore[arg-type]
            content_bytes = response.read()
            headers = response.headers
            charset_getter = getattr(headers, "get_content_charset", None)
            encoding = charset_getter() if callable(charset_getter) else None
            encoding = encoding or "utf-8"
            return content_bytes.decode(encoding, errors="ignore")
    except (URLError, OSError) as exc:
        logger.warning("Failed to fetch page %s: %s", url, exc)
        return None


def extract_links(html: str, base_url: str) -> Tuple[Set[str], Set[str]]:
    parser = LinkParser(base_url)
    parser.feed(html)
    return parser.links, parser.images


def fetch_image(url: str) -> Optional[int]:
    try:
        request = Request(url, headers={"User-Agent": "webcravl/1.0"})
        with urlopen(request, timeout=10) as response:  # type: ignore[arg-type]
            content_type = response.headers.get("Content-Type", "")
            if "jpeg" not in content_type.lower() and not is_jpeg_url(url):
                return None
            content = response.read()
            return len(content)
    except (URLError, OSError) as exc:
        logger.warning("Failed to fetch image %s: %s", url, exc)
        return None


def crawl_site(start_url: str, max_depth: int, min_size: int) -> List[ImageResult]:
    robots = RobotsHelper(start_url)
    queue: deque[Tuple[str, int]] = deque()
    queue.append((normalize_url(start_url), 0))
    visited_pages: Set[str] = set()
    found_images: List[ImageResult] = []

    while queue:
        current_url, depth = queue.popleft()
        if current_url in visited_pages or depth > max_depth:
            continue
        if not robots.can_fetch(current_url):
            logger.info("Skipping %s due to robots.txt", current_url)
            continue

        html = fetch_page(current_url)
        visited_pages.add(current_url)
        if html is None:
            continue

        page_links, image_links = extract_links(html, current_url)

        for image_url in image_links:
            size = fetch_image(image_url)
            if size is None:
                continue
            if size >= min_size:
                found_images.append(ImageResult(url=image_url, size_bytes=size))

        if depth < max_depth:
            for link in page_links:
                if link not in visited_pages:
                    queue.append((link, depth + 1))

    return found_images


__all__ = [
    "ImageResult",
    "RobotsHelper",
    "crawl_site",
    "extract_links",
    "fetch_image",
    "fetch_page",
    "is_jpeg_url",
    "normalize_url",
]

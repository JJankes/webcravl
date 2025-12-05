import argparse
import logging

from webcravl.crawler import ImageResult, crawl_site

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple JPEG crawler")
    parser.add_argument("start_url", nargs="?", help="Starting URL to crawl")
    parser.add_argument("-d", "--depth", type=int, default=1, help="Crawl depth")
    parser.add_argument(
        "-m",
        "--min-size",
        type=int,
        default=0,
        help="Minimum JPEG size in bytes",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Prompt for values instead of using command-line arguments",
    )
    return parser.parse_args()


def prompt_for_missing(args: argparse.Namespace) -> argparse.Namespace:
    if args.start_url and not args.interactive:
        return args

    args.start_url = args.start_url or input("Start URL: ")
    if args.depth is None or args.interactive:
        args.depth = int(input("Crawl depth (e.g. 1): "))
    if args.min_size is None or args.interactive:
        args.min_size = int(input("Minimum JPEG size in bytes: "))
    return args


def display_results(results: list[ImageResult], min_size: int) -> None:
    if not results:
        print("No JPEG images meeting the size threshold were found.")
        return

    print(f"Found {len(results)} JPEG images >= {min_size} bytes:\n")
    for result in results:
        print(f"- {result.url} ({result.size_bytes} bytes)")


def main() -> None:
    args = parse_args()
    args = prompt_for_missing(args)

    if not args.start_url:
        raise SystemExit("A start URL is required.")

    results = crawl_site(args.start_url, args.depth, args.min_size)
    display_results(results, args.min_size)


if __name__ == "__main__":
    main()

# webcravl

A small crawler that follows links from a starting URL, respects `robots.txt`, downloads JPEG images, and reports those meeting a minimum size. It can be run from the command line or with a simple Tkinter GUI suitable for Windows.

## Installation

The application only requires the standard library. To run tests, install `pytest`:

```bash
pip install -r requirements.txt
```

## Usage

### Command line

You can provide arguments directly or enable the interactive prompt with `--interactive`.

```bash
python -m src.main https://example.com -d 1 -m 1000
```

Interactive example:

```bash
python -m src.main --interactive
# Prompts for start URL, depth, and minimum size
```

### GUI (Windows-friendly)

Launch the Tkinter interface (works on Windows, macOS, and Linux with a standard Python install):

```bash
python -m src.gui
```

Enter the start URL, crawl depth, and minimum JPEG size, then click **Crawl** to see results in the window.

### How it works

The crawler will:
- Load and honor `robots.txt` for the host.
- Traverse links up to the specified depth (depth 0 crawls only the start page).
- Download JPEG images discovered on each page.
- Report images whose downloaded size is greater than or equal to the specified minimum number of bytes.

## Limitations

- Requests are synchronous and do not deduplicate image downloads across multiple references.
- Only JPEG images are considered, based on `Content-Type` or URL extension.
- Error handling is conservative; inaccessible pages or images are skipped.
- Large sites may take time to crawl; adjust depth to manage workload.

## Tests

Run the test suite with:

```bash
pytest
```

Tests rely on mocked HTTP responses and do not make network calls.

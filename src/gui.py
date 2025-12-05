"""Simple Tkinter GUI wrapper for the JPEG crawler.

This GUI is designed to run on Windows, macOS, and Linux with the standard
Python interpreter. It collects user inputs, runs the crawler in a background
thread, and displays the results in a scrollable text area.
"""
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import List

from webcravl.crawler import ImageResult, crawl_site


def format_results(results: List[ImageResult], min_size: int) -> str:
    if not results:
        return "No JPEG images meeting the size threshold were found."

    lines = [f"Found {len(results)} JPEG images >= {min_size} bytes:\n"]
    for result in results:
        lines.append(f"- {result.url} ({result.size_bytes} bytes)")
    return "\n".join(lines)


class CrawlerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("webcravl - JPEG crawler")
        self.root.geometry("640x480")

        main = ttk.Frame(root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # Inputs
        form = ttk.Frame(main)
        form.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(form, text="Start URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.url_var, width=50).grid(
            row=0, column=1, sticky=tk.EW, pady=2
        )

        ttk.Label(form, text="Depth:").grid(row=1, column=0, sticky=tk.W)
        self.depth_var = tk.StringVar(value="1")
        ttk.Entry(form, textvariable=self.depth_var, width=10).grid(
            row=1, column=1, sticky=tk.W, pady=2
        )

        ttk.Label(form, text="Min JPEG size (bytes):").grid(
            row=2, column=0, sticky=tk.W
        )
        self.size_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.size_var, width=15).grid(
            row=2, column=1, sticky=tk.W, pady=2
        )

        form.columnconfigure(1, weight=1)

        # Buttons
        button_row = ttk.Frame(main)
        button_row.pack(fill=tk.X)

        self.crawl_button = ttk.Button(button_row, text="Crawl", command=self.start_crawl)
        self.crawl_button.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(button_row, textvariable=self.status_var).pack(side=tk.RIGHT)

        # Results
        self.output = scrolledtext.ScrolledText(main, wrap=tk.WORD, height=18)
        self.output.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def start_crawl(self) -> None:
        start_url = self.url_var.get().strip()
        depth_text = self.depth_var.get().strip()
        size_text = self.size_var.get().strip()

        if not start_url:
            messagebox.showerror("Missing URL", "Please provide a start URL.")
            return

        try:
            depth = int(depth_text)
            min_size = int(size_text)
        except ValueError:
            messagebox.showerror(
                "Invalid input", "Depth and minimum size must be whole numbers."
            )
            return

        self.crawl_button.configure(state=tk.DISABLED)
        self.set_status("Crawling...")
        self.output.delete("1.0", tk.END)

        thread = threading.Thread(
            target=self._run_crawl, args=(start_url, depth, min_size), daemon=True
        )
        thread.start()

    def _run_crawl(self, start_url: str, depth: int, min_size: int) -> None:
        try:
            results = crawl_site(start_url, depth, min_size)
            text = format_results(results, min_size)
        except Exception as exc:  # pragma: no cover - GUI runtime protection
            text = f"Failed to crawl: {exc}"

        def update_ui() -> None:
            self.output.insert(tk.END, text)
            self.output.see(tk.END)
            self.crawl_button.configure(state=tk.NORMAL)
            self.set_status("Idle")

        self.root.after(0, update_ui)


def run() -> None:
    root = tk.Tk()
    CrawlerApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()

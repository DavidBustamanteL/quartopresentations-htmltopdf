#!/usr/bin/env python3
"""Export a local Quarto Reveal.js HTML deck to PDF with clickable TOC links.

Usage:
    python quarto_to_pdf.py presentation.html
    python quarto_to_pdf.py presentation.html -o presentation.pdf

Dependencies:
    python -m pip install playwright pymupdf beautifulsoup4
    python -m playwright install chromium

The HTML must be a *rendered* Quarto Reveal.js deck with its asset folder present.
The HTML ToC should contain ordinary anchors to section IDs (toc: true).
"""
import argparse
import contextlib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import threading
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
import pymupdf
from playwright.sync_api import sync_playwright


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def read_structure(html_path):
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    slides_root = soup.select_one(".reveal .slides")
    if not slides_root:
        raise ValueError("Not a Reveal.js deck: .reveal .slides was not found")
    slides = [s for s in slides_root.find_all("section") if not s.find("section", recursive=False)]
    id_to_page = {}
    for i, slide in enumerate(slides):
        if slide.get("id"):
            id_to_page[slide["id"]] = i
        for child in slide.find_all(id=True):
            id_to_page[child["id"]] = i
    entries = []
    toc = soup.select_one("#TOC, #table-of-contents, section.toc, nav[role='doc-toc']")
    # Quarto's Reveal TOC is typically #TOC, but detect a title-based section too.
    if toc is None:
        for s in slides:
            h = s.find(re.compile(r"^h[1-6]$"))
            if h and norm(h.get_text(" ", strip=True)).lower() in ("table of contents", "contents"):
                toc = s
                break
    if toc is not None:
        toc_slide = next((i for i, s in enumerate(slides) if s is toc or toc in s.descendants), None)
        if toc_slide is not None:
            for a in toc.select('a[href*="#"]'):
                url = a.get("href", "")
                target_id = unquote(urlsplit(url).fragment).lstrip("/")
                target_page = id_to_page.get(target_id)
                label = norm(a.get_text(" ", strip=True))
                if label and target_page is not None:
                    entries.append((toc_slide, label, target_page))
    return len(slides), entries


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def export_pdf(html_path, tmp_pdf, timeout_ms, chromium_path=None):
    handler = partial(QuietHandler, directory=str(html_path.parent))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        # Serving over HTTP ensures sibling CSS, fonts, JS and image assets resolve.
        url = f"http://127.0.0.1:{server.server_port}/{html_path.name}?print-pdf"
        with sync_playwright() as p:
            launch_opts = {"headless": True}
            if chromium_path:
                launch_opts["executable_path"] = chromium_path
            browser = p.chromium.launch(**launch_opts)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
                response = page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                if not response or not response.ok:
                    raise RuntimeError(f"Could not load deck: {url}")
                page.wait_for_function("window.Reveal && Reveal.isReady()", timeout=timeout_ms)
                page.evaluate("document.fonts.ready")
                page.wait_for_function(
                    "document.querySelectorAll('.reveal .slides section').length > 0", timeout=timeout_ms
                )
                # Ensure images are loaded before printing.
                page.evaluate("""async () => {
                    await Promise.all(Array.from(document.images).map(img => img.complete
                      ? Promise.resolve() : new Promise(resolve => {img.onload=resolve;img.onerror=resolve;})));
                }""")
                page.emulate_media(media="print")
                page.pdf(path=str(tmp_pdf), print_background=True, prefer_css_page_size=True,
                         scale=1, display_header_footer=False, margin={"top":"0", "bottom":"0", "left":"0", "right":"0"})
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def find_rect(page, label):
    # PDF text can vary in whitespace and line wrapping. Try exact, then fragments.
    for candidate in [label, norm(label), re.sub(r"^\d+\.?\s*", "", label)]:
        hits = page.search_for(candidate)
        if hits:
            return hits[0]
    # Fall back to first 35 characters: sufficiently distinctive for most TOCs.
    short = re.sub(r"^\d+\.?\s*", "", label)[:35].rstrip()
    hits = page.search_for(short) if short else []
    return hits[0] if hits else None


def visually_blank(page, threshold=0.002):
    """Detect a visually empty white page, even if PDF contains white rectangles.

    Render at low resolution and count sampled non-white pixels. The strict
    threshold avoids discarding pages with actual visible text or graphics.
    """
    pix = page.get_pixmap(matrix=pymupdf.Matrix(0.5, 0.5), colorspace=pymupdf.csRGB, alpha=False)
    data = pix.samples
    stride = pix.n  # three channels for RGB
    total = 0
    nonwhite = 0
    for i in range(0, len(data) - stride + 1, stride * 12):
        total += 1
        if min(data[i], data[i + 1], data[i + 2]) < 245:
            nonwhite += 1
    fraction = nonwhite / max(1, total)
    return fraction <= threshold, fraction


def link_toc(tmp_pdf, out_pdf, slide_count, entries, strict=False):
    doc = pymupdf.open(tmp_pdf)
    try:
        # Reveal/Chromium sometimes adds a trailing blank sheet whose PDF
        # contains an invisible/white background drawing. Check appearance,
        # not only the presence of drawing commands.
        while len(doc) > slide_count:
            last = doc[-1]
            blank, ink_fraction = visually_blank(last)
            if not blank:
                print(f"Extra page {len(doc)} has visible marks ({ink_fraction:.2%} sampled pixels); retaining it.")
                break
            print(f"Removing visually blank trailing PDF page {len(doc)}")
            doc.delete_page(len(doc) - 1)
        if len(doc) != slide_count:
            details = [f"page {i+1}: {len(pg.get_text().strip())} text characters"
                       for i, pg in enumerate(doc)]
            raise RuntimeError(
                f"PDF has {len(doc)} pages but HTML has {slide_count} slides. "
                "The extra page is not verified blank; refusing to make wrong links. "
                + "; ".join(details)
            )
        linked = 0
        bookmarks = []
        for toc_page, label, target in entries:
            rect = find_rect(doc[toc_page], label)
            if rect is None:
                print(f"WARNING: Could not locate printed ToC entry: {label!r}")
                continue
            doc[toc_page].insert_link({
                "kind": pymupdf.LINK_GOTO,
                "from": rect + (-2, -2, 2, 2),
                "page": target,
                "to": pymupdf.Point(0, 0),
                "zoom": 0,
            })
            linked += 1
            if (1, label, target + 1) not in bookmarks:
                bookmarks.append((1, label, target + 1))
        if strict and entries and linked != len(entries):
            raise RuntimeError(f"Only linked {linked} of {len(entries)} ToC entries")
        if bookmarks:
            doc.set_toc(bookmarks)
        doc.save(out_pdf, garbage=4, deflate=True)
        print(f"Created: {out_pdf} ({len(doc)} pages, {linked} clickable ToC links)")
        if not entries:
            print("NOTE: No HTML ToC anchors were found; PDF created without TOC links.")
    finally:
        doc.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, help="Rendered Quarto Reveal.js .html file")
    parser.add_argument("-o", "--output", type=Path, help="Output PDF (default: HTML name with .pdf)")
    parser.add_argument("--chromium", help="Explicit Chromium/Chrome executable path")
    parser.add_argument("--timeout", type=int, default=60000, help="Browser timeout in milliseconds")
    parser.add_argument("--strict-links", action="store_true", help="Fail if any TOC link cannot be located")
    args = parser.parse_args()
    html = args.html.expanduser().resolve()
    if not html.is_file():
        parser.error(f"HTML file not found: {html}")
    out = (args.output or html.with_suffix(".pdf")).expanduser().resolve()
    if out == html:
        parser.error("Output must differ from input")
    count, entries = read_structure(html)
    tmp = out.with_name(out.stem + ".tmp-export.pdf")
    try:
        export_pdf(html, tmp, args.timeout, args.chromium)
        link_toc(tmp, out, count, entries, args.strict_links)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except PermissionError:
            print(f"WARNING: Windows still has the temporary file open: {tmp}")
            print("Close any PDF preview of that file, then delete it manually.")


if __name__ == "__main__":
    main()

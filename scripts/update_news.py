#!/usr/bin/env python3
"""Atualiza no portal as seis notícias mais recentes do Município de Gouveia."""

from __future__ import annotations

import html
import re
import sys
import urllib.request
from pathlib import Path

NEWS_URL = "https://www.cm-gouveia.pt/noticias/"
INDEX = Path("index.html")
START = "<!-- NEWS:AUTO:START -->"
END = "<!-- NEWS:AUTO:END -->"

ARTICLE_RE = re.compile(
    r'<a\s+href="(https://www\.cm-gouveia\.pt/noticias/[^"]+/)"[^>]*>\s*'
    r'<div\s+class="newhome"\s+style="background-image:url\(([^)]+)\)"[^>]*>.*?'
    r'<div\s+class="newhtitle"[^>]*>\s*(.*?)\s*</div>',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")


def fetch_news() -> str:
    request = urllib.request.Request(
        NEWS_URL,
        headers={"User-Agent": "AssociativismoGouveia/1.0 (+GitHub Actions)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_title(raw: str) -> str:
    without_tags = TAG_RE.sub("", raw)
    return " ".join(html.unescape(without_tags).split())


def render_card(url: str, image: str, title: str) -> str:
    safe_url = html.escape(url, quote=True)
    safe_image = html.escape(html.unescape(image.strip().strip("'\"")), quote=True)
    safe_title = html.escape(title, quote=True)
    return (
        f'          <a class="news-card" href="{safe_url}" target="_blank" rel="noopener">'
        f'<img class="news-image" src="{safe_image}" alt="{safe_title}" loading="lazy">'
        f'<span class="news-date">Notícia municipal</span><h3>{safe_title}</h3>'
        f'<span class="news-more">Ler no site do Município <span>→</span></span></a>'
    )


def main() -> int:
    source = fetch_news()
    found = []
    seen = set()

    for url, image, raw_title in ARTICLE_RE.findall(source):
        if url in seen:
            continue
        title = clean_title(raw_title)
        if not title or not image:
            continue
        seen.add(url)
        found.append((url, image, title))
        if len(found) == 6:
            break

    if len(found) < 6:
        print(f"Erro: foram encontradas apenas {len(found)} notícias; o portal não foi alterado.", file=sys.stderr)
        return 1

    document = INDEX.read_text(encoding="utf-8")
    if START not in document or END not in document:
        print("Erro: marcadores automáticos não encontrados no index.html.", file=sys.stderr)
        return 1

    cards = "\n".join(render_card(*item) for item in found)
    updated = re.sub(
        rf"{re.escape(START)}.*?{re.escape(END)}",
        f"{START}\n{cards}\n          {END}",
        document,
        count=1,
        flags=re.DOTALL,
    )

    if updated == document:
        print("As notícias já estão atualizadas.")
        return 0

    INDEX.write_text(updated, encoding="utf-8")
    print("Notícias atualizadas com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Research Radar weekly scanner.

This script creates a candidate list only. It does not publish anything to the site.
The public Research Radar page reads from assets/research-radar-approved.json.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "assets" / "research-radar-config.json"
OUT_DIR = ROOT / "radar-candidates"
OPENALEX_ENDPOINT = "https://api.openalex.org/works"


def load_config() -> Dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def strip_abstract(inv: Optional[Dict[str, List[int]]]) -> str:
    if not inv:
        return ""
    words: Dict[int, str] = {}
    for word, positions in inv.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words))


def fetch_openalex(query: str, from_date: str, mailto: str, per_page: int = 20) -> List[Dict[str, Any]]:
    params = {
        "search": query,
        "filter": f"from_publication_date:{from_date}",
        "sort": "publication_date:desc",
        "per-page": str(per_page),
        "mailto": mailto,
    }
    url = OPENALEX_ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": f"research-radar/1.0 ({mailto})"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("results", [])
    except Exception as exc:
        print(f"Warning: failed query {query!r}: {exc}", file=sys.stderr)
        return []


def get_source_name(work: Dict[str, Any]) -> str:
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    return normalize_text(source.get("display_name"))


def get_publisher(work: Dict[str, Any]) -> str:
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    return normalize_text(source.get("host_organization_name") or source.get("publisher"))


def get_url(work: Dict[str, Any]) -> str:
    doi = normalize_text(work.get("doi"))
    if doi:
        return doi
    loc = work.get("primary_location") or {}
    landing = normalize_text(loc.get("landing_page_url"))
    if landing:
        return landing
    return normalize_text(work.get("id"))


def authors(work: Dict[str, Any], limit: int = 5) -> str:
    names = []
    for a in work.get("authorships", []):
        auth = a.get("author") or {}
        name = normalize_text(auth.get("display_name"))
        if name:
            names.append(name)
    if not names:
        return "Unknown author(s)"
    if len(names) > limit:
        return ", ".join(names[:limit]) + " et al."
    return ", ".join(names)


def contains_any(text: str, terms: Iterable[str]) -> bool:
    low = text.lower()
    return any(t.lower() in low for t in terms)


def score_work(work: Dict[str, Any], topic: Dict[str, Any], config: Dict[str, Any]) -> Tuple[int, List[str]]:
    title = normalize_text(work.get("display_name"))
    abstract = strip_abstract(work.get("abstract_inverted_index"))
    source = get_source_name(work)
    publisher = get_publisher(work)
    text = f"{title} {abstract} {source} {publisher}".lower()

    if contains_any(text, config.get("blocked_terms", [])):
        return -999, ["blocked term"]

    reasons: List[str] = []
    score = 0

    source_match = next((s for s in config.get("preferred_sources", []) if s.lower() == source.lower()), None)
    if source_match:
        score += 7
        reasons.append(f"preferred source: {source_match}")

    pub_match = next((p for p in config.get("preferred_publishers", []) if p.lower() in publisher.lower()), None)
    if pub_match:
        score += 5
        reasons.append(f"preferred publisher/institution: {pub_match}")

    keywords = topic.get("keywords", [])
    matched_keywords = [kw for kw in keywords if kw.lower() in text]
    if matched_keywords:
        score += min(6, 2 * len(matched_keywords))
        reasons.append("matches: " + ", ".join(matched_keywords[:4]))

    cited = int(work.get("cited_by_count") or 0)
    pub_date = normalize_text(work.get("publication_date"))
    try:
        age_days = (dt.date.today() - dt.date.fromisoformat(pub_date)).days
    except Exception:
        age_days = 9999

    if age_days <= 30:
        score += 2
        reasons.append("recent")
    elif age_days <= 180:
        score += 1

    if cited >= 10:
        score += 2
        reasons.append("early citation signal")
    elif cited >= 3:
        score += 1

    work_type = normalize_text(work.get("type"))
    if work_type in {"article", "book", "book-chapter", "report"}:
        score += 1
    elif work_type:
        score -= 1

    return score, reasons


def make_candidate(work: Dict[str, Any], topic: Dict[str, Any], score: int, reasons: List[str]) -> Dict[str, Any]:
    title = normalize_text(work.get("display_name")) or "Untitled"
    source = get_source_name(work) or get_publisher(work) or "Unknown source"
    year = work.get("publication_year") or "n.d."
    abstract = strip_abstract(work.get("abstract_inverted_index"))
    abstract_short = abstract[:450].rsplit(" ", 1)[0] + "…" if len(abstract) > 450 else abstract
    return {
        "id": normalize_text(work.get("id")) or get_url(work),
        "title": title,
        "authors": authors(work),
        "year": year,
        "source": source,
        "publisher": get_publisher(work),
        "type": normalize_text(work.get("type")),
        "date": normalize_text(work.get("publication_date")),
        "topic": topic.get("name", "Unclassified"),
        "url": get_url(work),
        "score": score,
        "reasons": reasons,
        "abstract": abstract_short,
    }


def collect_candidates(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    days_back = int(config.get("days_back", 14))
    from_date = (dt.date.today() - dt.timedelta(days=days_back)).isoformat()
    min_score = int(config.get("minimum_score", 9))
    max_candidates = int(config.get("max_candidates", 30))
    mailto = config.get("mailto", "example@example.com")

    by_id: Dict[str, Dict[str, Any]] = {}
    for topic in config.get("topics", []):
        for query in topic.get("queries", []):
            works = fetch_openalex(query, from_date, mailto, per_page=20)
            time.sleep(0.2)
            for work in works:
                score, reasons = score_work(work, topic, config)
                if score < min_score:
                    continue
                cand = make_candidate(work, topic, score, reasons)
                key = cand["id"] or cand["url"] or cand["title"].lower()
                if key not in by_id or cand["score"] > by_id[key]["score"]:
                    by_id[key] = cand

    candidates = sorted(by_id.values(), key=lambda c: (c["score"], c.get("date") or ""), reverse=True)
    return candidates[:max_candidates]


def render_markdown(candidates: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
    today = dt.date.today()
    iso_year, iso_week, _ = today.isocalendar()
    lines: List[str] = []
    lines.append(f"# Research Radar candidates — {iso_year} week {iso_week:02d}")
    lines.append("")
    lines.append("This file is generated automatically. It is a candidate list only; nothing here appears on the public website unless later added to `assets/research-radar-approved.json`.")
    lines.append("")
    lines.append("To curate, tell ChatGPT something like: `approve 2, 5, 9` or `hold 12`. Everything else can be ignored.")
    lines.append("")
    lines.append(f"Scan window: last {config.get('days_back', 14)} days. Maximum candidates shown: {config.get('max_candidates', 30)}.")
    lines.append("")

    if not candidates:
        lines.append("No candidates passed the current strict filters. This is not necessarily a problem; strict scanning should sometimes return nothing.")
        lines.append("")
        return "\n".join(lines)

    for i, c in enumerate(candidates, start=1):
        lines.append(f"## {i}. {c['title']}")
        lines.append("")
        lines.append(f"**Authors:** {c['authors']}")
        lines.append(f"**Year / date:** {c['year']} / {c.get('date') or 'n.d.'}")
        lines.append(f"**Source:** {c['source']}")
        if c.get("publisher"):
            lines.append(f"**Publisher / institution:** {c['publisher']}")
        lines.append(f"**Topic:** {c['topic']}")
        lines.append(f"**Why selected:** {'; '.join(c['reasons'])}.")
        lines.append(f"**Link:** {c['url']}")
        if c.get("abstract"):
            lines.append("")
            lines.append("**Abstract snippet:**")
            lines.append(c["abstract"])
        lines.append("")
        lines.append("**Decision:** approve / reject / hold")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    config = load_config()
    candidates = collect_candidates(config)
    OUT_DIR.mkdir(exist_ok=True)
    markdown = render_markdown(candidates, config)

    today = dt.date.today()
    iso_year, iso_week, _ = today.isocalendar()
    latest = OUT_DIR / "latest.md"
    weekly = OUT_DIR / f"{iso_year}-W{iso_week:02d}.md"
    latest.write_text(markdown, encoding="utf-8")
    weekly.write_text(markdown, encoding="utf-8")
    print(f"Wrote {latest} and {weekly} with {len(candidates)} candidates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

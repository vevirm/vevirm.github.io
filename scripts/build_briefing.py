#!/usr/bin/env python3
"""Build the Radar insights topic digest from the existing radar corpus.

The insights page is deliberately simple: it reads only material already admitted
to ``radar.json`` and groups each item under one primary subject heading. The
visible output is just topic headings and concise bullets drawn from the radar.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RADAR = ROOT / "radar.json"
OUT_DIR = ROOT / "briefing"
OUT_JSON = OUT_DIR / "briefing.json"
OUT_HTML = OUT_DIR / "index.html"

# Ordered for scanning/readability rather than by dynamic score.  Weights keep
# generic geopolitical words from overpowering a more concrete subject signal.
TOPICS: list[dict[str, Any]] = [
    {
        "key": "raw-materials",
        "name": "Raw materials",
        "terms": {
            "critical raw material": 8, "critical raw materials": 8, "raw material": 7,
            "rare earth": 8, "rare earths": 8, "mineral": 5, "minerals": 5,
            "lithium": 7, "cobalt": 7, "nickel": 6, "graphite": 7, "copper": 5,
            "gallium": 8, "germanium": 8, "tungsten": 7, "magnesium": 6,
            "battery material": 7, "mining": 6, "refining": 5,
        },
    },
    {
        "key": "research",
        "name": "Research",
        "terms": {
            "horizon europe": 8, "framework programme": 7, "framework program": 7,
            "erc": 7, "european research area": 7, "research funding": 6,
            "research infrastructure": 6, "research security": 7, "knowledge security": 7,
            "science diplomacy": 7, "scientific cooperation": 6, "research cooperation": 6,
            "research collaboration": 6, "academic": 4, "academia": 5, "university": 5,
            "universities": 5, "scientific": 3, "researcher": 4, "researchers": 4,
        },
    },
    {
        "key": "ai",
        "name": "AI",
        "terms": {
            "artificial intelligence": 9, " ai ": 8, "machine learning": 7,
            "foundation model": 8, "foundation models": 8, "large language model": 8,
            "llm": 8, "gpu": 7, "gpus": 7, "compute capacity": 7, "computing capacity": 7,
            "supercomputer": 6, "supercomputing": 6, "ai factory": 9, "ai factories": 9,
            "data centre": 4, "data center": 4,
        },
    },
    {
        "key": "chips-quantum",
        "name": "Chips & quantum",
        "terms": {
            "semiconductor": 9, "semiconductors": 9, "microelectronics": 8,
            "chip": 7, "chips": 7, "quantum": 9, "photonics": 8,
            "critical technology": 6, "critical technologies": 6,
            "advanced technology": 4, "advanced technologies": 4,
        },
    },
    {
        "key": "energy",
        "name": "Energy",
        "terms": {
            "energy security": 8, "energy": 4, "nuclear": 7, "smr": 8,
            "small modular reactor": 8, "hydrogen": 7, "renewable": 5, "renewables": 5,
            "electricity grid": 7, "power grid": 7, "grid": 4, "battery": 5,
            "clean tech": 6, "cleantech": 6, "climate technology": 6, "climate tech": 6,
            "carbon capture": 6, "fusion": 7,
        },
    },
    {
        "key": "security-defence",
        "name": "Security & defence",
        "terms": {
            "defence": 8, "defense": 8, "dual-use": 8, "dual use": 8,
            "military": 8, "nato": 7, "security screening": 6, "export control": 6,
            "export controls": 6, "foreign interference": 7, "knowledge leakage": 7,
            "cybersecurity": 6, "cyber security": 6, "economic coercion": 5,
        },
    },
    {
        "key": "trade-industry",
        "name": "Trade & industry",
        "terms": {
            "economic security": 7, "industrial policy": 7, "industrial competitiveness": 7,
            "competitiveness": 5, "manufacturing": 5, "supply chain": 4,
            "supply chains": 4, "trade": 4, "tariff": 6, "tariffs": 6,
            "investment screening": 7, "foreign direct investment": 6, "fdi": 5,
            "sanction": 5, "sanctions": 5, "strategic autonomy": 6,
            "strategic dependency": 6, "strategic dependencies": 6,
            "de-risking": 6, "derisking": 6, "de-risk": 6,
        },
    },
    {
        "key": "digital-cyber",
        "name": "Digital & cyber",
        "terms": {
            "digital infrastructure": 8, "cloud": 5, "cloud infrastructure": 7,
            "telecom": 6, "telecommunications": 6, "5g": 6, "6g": 7,
            "submarine cable": 7, "subsea cable": 7, "data governance": 6,
            "data space": 6, "digital sovereignty": 7, "platform": 3,
            "cyber": 5, "network security": 6,
        },
    },
    {
        "key": "space",
        "name": "Space",
        "terms": {
            "space": 7, "satellite": 8, "satellites": 8, "launch vehicle": 8,
            "launcher": 7, "esa": 7, "copernicus": 8, "galileo": 8,
            "earth observation": 7, "orbital": 7,
        },
    },
    {
        "key": "health-biotech",
        "name": "Health & biotech",
        "terms": {
            "biotech": 8, "biotechnology": 8, "biological": 4, "life science": 6,
            "life sciences": 6, "health security": 7, "health": 4, "pharma": 6,
            "pharmaceutical": 6, "pharmaceuticals": 6, "vaccine": 7, "vaccines": 7,
            "biomedical": 7, "genomic": 7, "genomics": 7, "bioeconomy": 6,
        },
    },
    {
        "key": "talent",
        "name": "Talent & skills",
        "terms": {
            "talent": 7, "skills": 6, "researcher mobility": 8, "scientist mobility": 8,
            "brain drain": 8, "brain gain": 8, "visa": 6, "visas": 6,
            "education": 4, "doctoral": 5, "phd": 5, "migration": 4,
            "workforce": 5, "training": 4,
        },
    },
    {
        "key": "international",
        "name": "International partnerships",
        "terms": {
            "global gateway": 8, "indo-pacific": 7, "international cooperation": 6,
            "international partnership": 7, "international partnerships": 7,
            "association agreement": 7, "associated country": 6,
            "china": 3, "chinese": 3, "united states": 3, " u.s. ": 3, " us ": 2,
            "japan": 3, "south korea": 3, "korea": 2, "india": 3, "taiwan": 3,
            "ukraine": 3, "russia": 3, "africa": 3, "latin america": 3,
        },
    },
    {
        "key": "foresight",
        "name": "Foresight",
        "terms": {
            "foresight": 9, "horizon scanning": 9, "scenario planning": 8,
            "scenario": 6, "scenarios": 6, "weak signal": 8, "weak signals": 8,
            "delphi": 8, "backcasting": 8, "anticipatory governance": 8,
            "strategic intelligence": 6, "futures literacy": 8,
        },
    },
]

OTHER_TOPIC = {"key": "other", "name": "Other"}


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def normalise(v: Any) -> str:
    s = clean(v).lower().replace("–", "-").replace("—", "-")
    return " " + re.sub(r"[^a-z0-9+.#/-]+", " ", s) + " "


def item_text(item: dict[str, Any]) -> str:
    return " ".join(clean(item.get(k)) for k in (
        "title", "headline", "summary", "relevance_note", "signal_note", "anchor", "source", "type"
    ))


def label(item: dict[str, Any]) -> str:
    return clean(item.get("title") or item.get("headline") or "Untitled item")


def source_label(item: dict[str, Any]) -> str:
    return clean(item.get("source"))


def note_for(item: dict[str, Any], limit: int = 620) -> str:
    # Keep this as source/radar wording. No generated interpretation is inserted.
    note = clean(item.get("signal_note") or item.get("summary") or item.get("relevance_note"))
    if not note:
        return ""
    if len(note) <= limit:
        return note
    cut = note[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:") + "…"


def relevance_for(item: dict[str, Any], limit: int = 360) -> str:
    rel = clean(item.get("relevance_note"))
    if not rel or rel == clean(item.get("summary")):
        return ""
    if len(rel) <= limit:
        return rel
    return rel[:limit].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def current_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for strand in ("strand_a", "strand_b"):
        vals = data.get(strand) if isinstance(data.get(strand), list) else []
        for raw in vals:
            x = dict(raw)
            x["_strand"] = "A" if strand.endswith("a") else "B"
            x["_fresh"] = bool(x.get("new_this_scan"))
            items.append(x)
    vals = data.get("strand_c") if isinstance(data.get("strand_c"), list) else []
    for raw in vals:
        x = dict(raw)
        x["_strand"] = "C"
        x["_fresh"] = True
        items.append(x)
    return items


def topic_scores(item: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    text = normalise(item_text(item))
    scores: list[tuple[int, dict[str, Any]]] = []
    for topic in TOPICS:
        score = 0
        for term, weight in topic["terms"].items():
            needle = normalise(term)
            if needle.strip() and needle in text:
                score += int(weight)
        if score:
            scores.append((score, topic))
    scores.sort(key=lambda x: x[0], reverse=True)
    return scores


def public_item(item: dict[str, Any]) -> dict[str, Any]:
    """Return only the text needed by the deliberately minimal insights page."""
    return {
        "title": label(item),
        "detail": note_for(item, limit=360),
    }


def make_briefing(data: dict[str, Any]) -> dict[str, Any]:
    items = current_items(data)
    buckets: dict[str, list[dict[str, Any]]] = {t["key"]: [] for t in TOPICS}
    buckets[OTHER_TOPIC["key"]] = []

    for item in items:
        scores = topic_scores(item)
        primary = scores[0][1] if scores else OTHER_TOPIC
        buckets[primary["key"]].append(item)

    def sort_key(x: dict[str, Any]) -> tuple[int, str, str]:
        return (
            1 if x.get("_fresh") else 0,
            clean(x.get("date")),
            label(x).lower(),
        )

    topics: list[dict[str, Any]] = []
    for topic in [*TOPICS, OTHER_TOPIC]:
        vals = sorted(buckets[topic["key"]], key=sort_key, reverse=True)
        if vals:
            topics.append({
                "key": topic["key"],
                "name": topic["name"],
                "items": [public_item(x) for x in vals],
            })

    return {
        "radar_last_updated": data.get("last_updated"),
        "topics": topics,
    }


def esc(v: Any) -> str:
    return html.escape(clean(v), quote=True)


def item_html(item: dict[str, Any]) -> str:
    title = esc(item.get("title"))
    detail = esc(item.get("detail"))
    if detail:
        return f'<li><strong>{title}</strong> — {detail}</li>'
    return f'<li>{title}</li>'


def render_page(briefing: dict[str, Any]) -> str:
    sections: list[str] = []
    for topic in briefing.get("topics", []):
        items = "".join(item_html(x) for x in topic.get("items", []))
        if items:
            sections.append(
                f'<section id="{esc(topic.get("key"))}"><h2>{esc(topic.get("name"))}</h2><ul>{items}</ul></section>'
            )
    if not sections:
        sections.append('<p class="empty">No radar signals are available yet.</p>')

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>Radar insights</title>
<style>
:root{{--bg:#f6f5f1;--paper:#fff;--text:#181817;--muted:#6c6962;--line:#ddd9cf;--accent:#6d1f27;--max:880px}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:17px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}.wrap{{width:min(calc(100% - 32px),var(--max));margin:auto}}header{{padding:34px 0 24px;border-bottom:1px solid var(--line);background:var(--paper)}}.kicker{{font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}}h1{{font-size:clamp(2.2rem,6vw,4rem);line-height:1;letter-spacing:-.05em;margin:.15em 0 .2em}}.lede{{margin:0;color:var(--muted)}}.back{{display:inline-block;margin-top:16px;color:var(--muted);text-decoration:none;font-size:.86rem}}main{{padding:8px 0 56px}}section{{padding:26px 0 20px;border-bottom:1px solid var(--line)}}section:last-child{{border-bottom:0}}h2{{font-size:1.45rem;letter-spacing:-.025em;margin:0 0 10px}}ul{{margin:0;padding-left:1.25em}}li{{margin:.55em 0}}strong{{font-weight:750}}.empty{{color:var(--muted);padding:28px 0}}@media(max-width:640px){{body{{font-size:16px}}section{{padding:22px 0 16px}}}}
</style>
</head>
<body>
<header><div class="wrap">
  <div class="kicker">Radar insights</div>
  <h1>Signals by topic</h1>
  <p class="lede">The radar grouped into simple topic bullets.</p>
  <a class="back" href="../">← Main radar</a>
</div></header>
<main class="wrap">{''.join(sections)}</main>
</body></html>"""


def main() -> int:
    if not RADAR.exists():
        raise SystemExit("radar.json not found")
    data = json.loads(RADAR.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    briefing = make_briefing(data)
    OUT_JSON.write_text(json.dumps(briefing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_HTML.write_text(render_page(briefing), encoding="utf-8")
    print(f"Built {OUT_HTML.relative_to(ROOT)} with {len(briefing['topics'])} populated topic(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

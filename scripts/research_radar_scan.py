#!/usr/bin/env python3
"""
Research Radar weekly scanner.

This script creates a candidate list only. It does not publish anything to the site.
The public Research Radar page reads from assets/research-radar-approved.json.

The scanner is deliberately conservative. It first applies a publication-type and
substance gate, then scores topical relevance and source quality. This is meant to
avoid thin web material, news/blog/vendor pages, and quirky low-substance hits that
only match a keyword.
"""
from __future__ import annotations

import datetime as dt
import json
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

ARTICLE_TYPES = {"article", "journal-article", "review", "review-article"}
BOOK_TYPES = {"book", "book-chapter", "book-section", "book-part", "monograph", "edited-book"}
REPORT_TYPES = {"report", "report-component"}
BORDERLINE_TYPES = {"preprint", "working-paper", "working paper", "posted-content"}


def load_config() -> Dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(value: Optional[Any]) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def strip_abstract(inv: Optional[Dict[str, List[int]]]) -> str:
    if not inv:
        return ""
    words: Dict[int, str] = {}
    for word, positions in inv.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words))


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def fetch_openalex(query: str, from_date: str, mailto: str, per_page: int = 25) -> List[Dict[str, Any]]:
    params = {
        "search": query,
        "filter": f"from_publication_date:{from_date}",
        "sort": "publication_date:desc",
        "per-page": str(per_page),
        "mailto": mailto,
    }
    url = OPENALEX_ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": f"research-radar/1.1 ({mailto})"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("results", [])
    except Exception as exc:
        print(f"Warning: failed query {query!r}: {exc}", file=sys.stderr)
        return []


def primary_source(work: Dict[str, Any]) -> Dict[str, Any]:
    loc = work.get("primary_location") or {}
    return loc.get("source") or {}


def get_source_name(work: Dict[str, Any]) -> str:
    return normalize_text(primary_source(work).get("display_name"))


def get_source_type(work: Dict[str, Any]) -> str:
    return normalize_text(primary_source(work).get("type")).lower()


def get_publisher(work: Dict[str, Any]) -> str:
    source = primary_source(work)
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


def url_domain(url: str) -> str:
    if not url:
        return ""
    if url.startswith("doi:"):
        return "doi.org"
    parsed = urllib.parse.urlparse(url if "://" in url else "https://" + url)
    return parsed.netloc.lower().removeprefix("www.")


def work_domains(work: Dict[str, Any]) -> List[str]:
    urls = [get_url(work)]
    loc = work.get("primary_location") or {}
    urls.extend([normalize_text(loc.get("landing_page_url")), normalize_text(loc.get("pdf_url"))])
    for location in work.get("locations", []) or []:
        urls.extend([normalize_text(location.get("landing_page_url")), normalize_text(location.get("pdf_url"))])
    domains: List[str] = []
    for url in urls:
        domain = url_domain(url)
        if domain and domain not in domains:
            domains.append(domain)
    return domains


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


def has_authors(work: Dict[str, Any]) -> bool:
    return authors(work) != "Unknown author(s)"


def contains_any(text: str, terms: Iterable[str]) -> bool:
    low = (text or "").lower()
    return any(t.lower() in low for t in terms if t)


def list_matches(texts: Iterable[str], patterns: Iterable[str]) -> List[str]:
    haystack = " ".join(t for t in texts if t).lower()
    return [p for p in patterns if p and p.lower() in haystack]


def type_labels(work: Dict[str, Any]) -> List[str]:
    labels = [
        normalize_text(work.get("type")),
        normalize_text(work.get("type_crossref")),
        get_source_type(work),
    ]
    return [x.lower().replace("_", "-") for x in labels if x]


def referenced_work_count(work: Dict[str, Any]) -> int:
    count = work.get("referenced_works_count")
    if isinstance(count, int):
        return count
    refs = work.get("referenced_works") or []
    return len(refs) if isinstance(refs, list) else 0


def preferred_source_match(work: Dict[str, Any], config: Dict[str, Any]) -> Optional[str]:
    source = get_source_name(work)
    return next((s for s in config.get("preferred_sources", []) if s.lower() == source.lower()), None)


def preferred_publisher_match(work: Dict[str, Any], config: Dict[str, Any]) -> Optional[str]:
    publisher = get_publisher(work)
    source = get_source_name(work)
    return next(
        (p for p in config.get("preferred_publishers", []) if p.lower() in f"{publisher} {source}".lower()),
        None,
    )


def domain_match(work: Dict[str, Any], domains: Iterable[str]) -> Optional[str]:
    work_domain_list = work_domains(work)
    for allowed in domains:
        allowed_l = allowed.lower().removeprefix("www.")
        for domain in work_domain_list:
            if domain == allowed_l or domain.endswith("." + allowed_l):
                return allowed
    return None


def source_has_doaj_signal(work: Dict[str, Any]) -> bool:
    source = primary_source(work)
    return bool(source.get("is_in_doaj"))


def is_title_listicle_or_clickbait(title: str, markers: Iterable[str]) -> bool:
    low = title.lower()
    if contains_any(low, markers):
        return True
    listicle_patterns = [
        r"^\s*top\s+\d+\b",
        r"^\s*\d+\s+(trends|things|ways|tips|reasons)\b",
        r"\b(trends|things)\s+to\s+watch\b",
        r"\bwhat\s+you\s+need\s+to\s+know\b",
    ]
    return any(re.search(pat, low) for pat in listicle_patterns)


def hard_exclusion_reasons(work: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    title = normalize_text(work.get("display_name"))
    source = get_source_name(work)
    publisher = get_publisher(work)
    domains = work_domains(work)
    gate = config.get("quality_gate", {})

    reasons: List[str] = []
    if work.get("is_retracted"):
        reasons.append("retracted work")

    excluded_domain = domain_match(work, gate.get("excluded_domains", []))
    if excluded_domain:
        reasons.append(f"excluded domain: {excluded_domain}")

    source_patterns = gate.get("excluded_source_patterns", []) + config.get("blocked_terms", [])
    matched_sources = list_matches([title, source, publisher, " ".join(domains)], source_patterns)
    if matched_sources:
        reasons.append("excluded source/title signal: " + ", ".join(matched_sources[:3]))

    if is_title_listicle_or_clickbait(title, gate.get("listicle_markers", [])):
        reasons.append("listicle/clickbait title")

    bad_source_types = {s.lower() for s in gate.get("excluded_source_types", [])}
    if get_source_type(work) in bad_source_types:
        reasons.append(f"excluded source type: {get_source_type(work)}")

    return reasons


def publication_type_gate(work: Dict[str, Any], config: Dict[str, Any]) -> Tuple[bool, str]:
    """Return whether the item is one of the admitted publication types."""
    gate = config.get("quality_gate", {})
    labels = set(type_labels(work))
    doi = bool(normalize_text(work.get("doi")))
    source = get_source_name(work)
    publisher_match = preferred_publisher_match(work, config)
    source_match = preferred_source_match(work, config)
    institutional_domain = domain_match(work, gate.get("institutional_domains", []))
    academic_domain = domain_match(work, gate.get("academic_publisher_domains", []))
    recognised_domain = domain_match(work, gate.get("recognised_research_domains", []))
    source_text = f"{source} {get_publisher(work)}"
    institutional_name = list_matches([source_text], gate.get("institutional_publishers", []))
    recognised_name = list_matches([source_text], gate.get("recognised_research_groups", []))
    source_type = get_source_type(work)

    if labels & ARTICLE_TYPES:
        known_venue = bool(source_match or publisher_match or academic_domain or source_has_doaj_signal(work))
        requires_known_venue = bool(gate.get("article_requires_known_venue", True))
        if doi and source and source_type not in {"repository", "blog", "newspaper", "magazine"}:
            if not requires_known_venue or known_venue:
                if source_match:
                    qualifier = "preferred journal"
                elif publisher_match or academic_domain:
                    qualifier = "academic-publisher journal article"
                elif source_has_doaj_signal(work):
                    qualifier = "DOAJ/indexed journal article"
                else:
                    qualifier = "DOI/indexed article"
                return True, qualifier
            return False, "article venue not recognised by source/publisher/DOAJ whitelist"
        return False, "article without DOI or scholarly source"

    if labels & BOOK_TYPES:
        if publisher_match or academic_domain:
            return True, "academic book/chapter publisher"
        return False, "book/chapter publisher not on academic whitelist"

    if labels & REPORT_TYPES:
        if institutional_domain or institutional_name:
            return True, "authoritative institutional/sector report"
        # Some reports are issued by major academic publishers.
        if publisher_match or academic_domain:
            return True, "academic-publisher report"
        return False, "report source not recognised as institutional/academic"

    if labels & BORDERLINE_TYPES:
        if recognised_domain or recognised_name or institutional_domain or institutional_name:
            return True, "borderline item from recognised research body"
        return False, "borderline/preprint source not recognised"

    return False, "publication type not admitted: " + (", ".join(sorted(labels)) or "unknown")


def substance_gate(work: Dict[str, Any], config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    gate = config.get("quality_gate", {})
    title = normalize_text(work.get("display_name"))
    abstract = strip_abstract(work.get("abstract_inverted_index"))
    text = f"{title} {abstract}"
    min_words = int(gate.get("min_abstract_words", 80))
    min_refs = int(gate.get("min_references", 8))
    min_signals = int(gate.get("min_substance_signals", 4))

    signals: List[str] = []
    if has_authors(work) or get_publisher(work):
        signals.append("accountable author/organisation")
    if normalize_text(work.get("doi")) or source_has_doaj_signal(work):
        signals.append("DOI/indexing signal")
    if referenced_work_count(work) >= min_refs:
        signals.append(f"reference list signal ({referenced_work_count(work)} refs)")
    if word_count(abstract) >= min_words:
        signals.append(f"developed abstract ({word_count(abstract)} words)")
    if contains_any(text, gate.get("method_terms", [])):
        signals.append("method/evidence language")
    if contains_any(text, gate.get("analysis_terms", [])):
        signals.append("analysis/findings/synthesis language")
    if preferred_source_match(work, config) or preferred_publisher_match(work, config) or domain_match(work, gate.get("institutional_domains", [])):
        signals.append("scholarly/policy venue signal")

    return len(signals) >= min_signals, signals


def quality_gate(work: Dict[str, Any], config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    exclusions = hard_exclusion_reasons(work, config)
    if exclusions:
        return False, exclusions

    publication_ok, publication_reason = publication_type_gate(work, config)
    if not publication_ok:
        return False, [publication_reason]

    substance_ok, signals = substance_gate(work, config)
    if not substance_ok:
        needed = config.get("quality_gate", {}).get("min_substance_signals", 4)
        return False, [publication_reason, f"substance gate failed ({len(signals)}/{needed} signals)"] + signals

    return True, [publication_reason] + signals


def score_work(work: Dict[str, Any], topic: Dict[str, Any], config: Dict[str, Any]) -> Tuple[int, List[str]]:
    title = normalize_text(work.get("display_name"))
    abstract = strip_abstract(work.get("abstract_inverted_index"))
    source = get_source_name(work)
    publisher = get_publisher(work)
    text = f"{title} {abstract} {source} {publisher}".lower()

    accepted, quality_reasons = quality_gate(work, config)
    if not accepted:
        return -999, quality_reasons

    reasons: List[str] = ["quality gate: " + "; ".join(quality_reasons[:4])]
    score = 8

    source_match = preferred_source_match(work, config)
    if source_match:
        score += 7
        reasons.append(f"preferred source: {source_match}")

    pub_match = preferred_publisher_match(work, config)
    if pub_match:
        score += 5
        reasons.append(f"preferred publisher/institution: {pub_match}")

    keywords = topic.get("keywords", [])
    matched_keywords = [kw for kw in keywords if kw.lower() in text]
    if matched_keywords:
        score += min(6, 2 * len(matched_keywords))
        reasons.append("topic match: " + ", ".join(matched_keywords[:4]))

    pub_date = normalize_text(work.get("publication_date"))
    try:
        age_days = (dt.date.today() - dt.date.fromisoformat(pub_date)).days
    except Exception:
        age_days = 9999

    if age_days <= 30:
        score += 3
        reasons.append("recent")
    elif age_days <= 180:
        score += 1

    cited = int(work.get("cited_by_count") or 0)
    refs = referenced_work_count(work)
    if cited >= 10:
        score += 2
        reasons.append("early citation signal")
    elif cited >= 3:
        score += 1
    if refs >= 30:
        score += 2
        reasons.append("substantial references")
    elif refs >= 12:
        score += 1

    return score, reasons


def make_candidate(work: Dict[str, Any], topic: Dict[str, Any], score: int, reasons: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    title = normalize_text(work.get("display_name")) or "Untitled"
    source = get_source_name(work) or get_publisher(work) or "Unknown source"
    year = work.get("publication_year") or "n.d."
    abstract = strip_abstract(work.get("abstract_inverted_index"))
    abstract_short = abstract[:450].rsplit(" ", 1)[0] + "…" if len(abstract) > 450 else abstract
    _, quality_reasons = quality_gate(work, config)
    return {
        "id": normalize_text(work.get("id")) or get_url(work),
        "title": title,
        "authors": authors(work),
        "year": year,
        "source": source,
        "publisher": get_publisher(work),
        "type": normalize_text(work.get("type")),
        "type_crossref": normalize_text(work.get("type_crossref")),
        "source_type": get_source_type(work),
        "date": normalize_text(work.get("publication_date")),
        "topic": topic.get("name", "Unclassified"),
        "url": get_url(work),
        "score": score,
        "reasons": reasons,
        "quality_signals": quality_reasons,
        "references": referenced_work_count(work),
        "abstract_words": word_count(abstract),
        "abstract": abstract_short,
    }


def collect_candidates(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    days_back = int(config.get("days_back", 14))
    from_date = (dt.date.today() - dt.timedelta(days=days_back)).isoformat()
    min_score = int(config.get("minimum_score", 13))
    max_candidates = int(config.get("max_candidates", 30))
    mailto = config.get("mailto", "example@example.com")
    per_page = int(config.get("openalex_per_query", 25))

    by_id: Dict[str, Dict[str, Any]] = {}
    rejected_counts: Dict[str, int] = {}
    for topic in config.get("topics", []):
        for query in topic.get("queries", []):
            works = fetch_openalex(query, from_date, mailto, per_page=per_page)
            time.sleep(0.2)
            for work in works:
                score, reasons = score_work(work, topic, config)
                if score < min_score:
                    if score <= -999 and reasons:
                        key = reasons[0]
                        rejected_counts[key] = rejected_counts.get(key, 0) + 1
                    continue
                cand = make_candidate(work, topic, score, reasons, config)
                key = cand["id"] or cand["url"] or cand["title"].lower()
                if key not in by_id or cand["score"] > by_id[key]["score"]:
                    by_id[key] = cand

    if rejected_counts:
        print("Quality-gate rejections:")
        for reason, count in sorted(rejected_counts.items(), key=lambda item: item[1], reverse=True)[:12]:
            print(f"  {count:3d}  {reason}")

    candidates = sorted(by_id.values(), key=lambda c: (c["score"], c.get("date") or ""), reverse=True)
    return candidates[:max_candidates]


def render_markdown(candidates: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
    today = dt.date.today()
    iso_year, iso_week, _ = today.isocalendar()
    gate = config.get("quality_gate", {})
    lines: List[str] = []
    lines.append(f"# Research Radar candidates — {iso_year} week {iso_week:02d}")
    lines.append("")
    lines.append("This file is generated automatically. It is a candidate list only; nothing here appears on the public website unless later added to `assets/research-radar-approved.json`.")
    lines.append("")
    lines.append("The scanner now applies a hard publication-type gate and a substance gate before topical scoring. This should exclude news, blogs, vendor material, listicles, weak preprints, and thin conceptual/prospecting pieces.")
    lines.append("")
    lines.append("To curate, tell ChatGPT something like: `approve 2, 5, 9` or `hold 12`. Everything else can be ignored.")
    lines.append("")
    lines.append(f"Scan window: last {config.get('days_back', 14)} days. Maximum candidates shown: {config.get('max_candidates', 30)}. Minimum score: {config.get('minimum_score', 13)}. Substance gate: at least {gate.get('min_substance_signals', 4)} signals.")
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
        lines.append(f"**Type:** {c.get('type') or 'n.d.'}; source type: {c.get('source_type') or 'n.d.'}; references: {c.get('references', 0)}; abstract words: {c.get('abstract_words', 0)}")
        lines.append(f"**Topic:** {c['topic']}")
        lines.append(f"**Quality gate:** {'; '.join(c.get('quality_signals', [])[:6])}.")
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

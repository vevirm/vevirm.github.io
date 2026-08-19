RADAR INSIGHTS — SIMPLE TOPIC VIEW
==================================

Purpose
-------
Radar insights is a deliberately simple subject view of the material already
admitted to radar.json. It is not a second scanner and it does not create a
second analytical layer.

The page contains only topic headings and bullets, for example:
- Raw materials
- Research
- AI
- Chips & quantum
- Energy
- Security & defence
- Trade & industry
- Digital & cyber
- Space
- Health & biotech
- Talent & skills
- International partnerships
- Foresight

Each radar item is assigned to one primary topic so it appears only once. The
visible bullet is built only from the title and short note/summary already in the
main radar. The insights page does not show sources, dates, links, strands,
anchors, tags, counts, evidence panels or extra interpretation.

Timing and safety
-----------------
The existing briefing workflow runs after successful radar scans. It reads
radar.json and writes only briefing/index.html and briefing/briefing.json. The
workflow checks the radar checksum before and after building so the scanner
corpus is not modified.

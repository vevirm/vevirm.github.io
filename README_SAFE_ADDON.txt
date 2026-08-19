RADAR INSIGHTS — SIMPLE TOPIC VIEW
==================================

Radar Insights is deliberately only a second VIEW of the existing radar.json.
It is not a second scanner and there is no generated briefing database.

The page reads radar.json directly in the browser and shows only:

    Raw materials
    - short bullet
    - short bullet

    Research
    - short bullet

    AI
    - short bullet

plus the other relevant topic headings.

It does NOT display sources, dates, links, Strand labels, anchors, relevance
notes, tags, counts, evidence cards, methodology panels or topic navigation.
Each radar item is shown once under its strongest topic.

The workflow .github/workflows/radar-briefing.yml is publish-only. It cannot
rewrite briefing/index.html and cannot modify radar.json. It simply requests a
GitHub Pages rebuild after the page is changed or after a successful radar scan.

# Veli Virmajoki Academic Site

Static GitHub Pages site.

## Main pages

- `index.html` — homepage, redesigned as an intellectual doorway into the work.
- `research.html` — ideas, methods, concepts, and keyword-rich research map.
- `publications.html` — formal publication list, rendered from `assets/site-data.js`.
- `cv.html` — academic CV.
- `engagement.html` — public engagement and professional outputs.
- `contact.html` — contact information.

## Editing

- Main publication and CV data: `assets/site-data.js`
- Visual design and layout: `assets/styles.css`
- Interactive behaviour: `assets/main.js`

The current visual identity uses white, red, and black, with spacious sections and restrained typography.


Added Research Radar:
- research-radar.html
- assets/research-radar-approved.json


Research Radar is now visible in the top navigation as Radar and has a stronger homepage callout.


## Research Radar weekly candidates

This site includes a Research Radar page (`research-radar.html`) and a weekly candidate-scan system.

The public page shows only items in:

```text
assets/research-radar-approved.json
```

The automatic scanner creates candidate lists in:

```text
radar-candidates/latest.md
```

The candidate list is for review only. To curate it, open `radar-candidates/latest.md`, choose item numbers, and use a note such as:

```text
approve 2, 5, 9
hold 12
reject the rest
```

The weekly scan is configured in:

```text
assets/research-radar-config.json
scripts/research_radar_scan.py
.github/workflows/research-radar.yml
```

The workflow runs weekly and can also be started manually from GitHub Actions.

### Scanner focus after the strict-theme update

The weekly scanner is not a general “interesting new papers” feed. It now applies a site-focus gate after the publication/substance gate. A candidate must be close to the themes of this site: futures/foresight methods, Delphi, scenario work, horizon scanning, narrative foresight, philosophy of futures studies, philosophy/futures of science, historiography/counterfactuals/conceivability, or system-level futures of work and universities.

This means that a peer-reviewed empirical article can still be rejected if it is merely a good qualitative study about an unrelated applied topic. The scanner now rejects micro-experience/domain-drift papers unless they clearly contribute to the site's methods, concepts, policy/system analysis, or core futures/philosophy themes.

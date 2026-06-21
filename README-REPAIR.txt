Research Radar page repair package

Replace these files in the GitHub repository:

research-radar.html
assets/main.js
assets/styles.css
assets/research-radar-approved.json

The important repair is assets/research-radar-approved.json:
- removes the accidental nested "items" block
- restores the original 30 curated items
- adds approved candidates 4, 8, and 13 under the correct topics

If you only want the minimum fix, replace only:
assets/research-radar-approved.json

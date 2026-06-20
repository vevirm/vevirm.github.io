# Veli Virmajoki academic website

This is a static academic website prototype built from the provided University of Turku profile, CV, publication list, and application vision material.

## Files

- `index.html` — landing page
- `publications.html` — filterable publication list, separated into peer-reviewed, books, non-refereed scientific work, and professional/stakeholder outputs
- `cv.html` — public-facing academic CV summary
- `engagement.html` — LinkedIn/blog/public engagement page
- `assets/site-data.js` — editable data source for profile, publications, CV, vision, and curated updates
- `assets/styles.css` — visual design
- `assets/main.js` — filtering, rendering, copy-citation buttons, mobile menu

## How to edit content

Most content is in `assets/site-data.js`. You can update publications, profile links, and LinkedIn cards there without touching the HTML.

The LinkedIn section is intentionally curated rather than automatically embedded. A fully automatic feed requires approved LinkedIn API access and a server-side integration.

## Privacy note

The public CV page includes the public University of Turku email address but omits the phone number from the uploaded CV. Add it only if you want it publicly visible.

## Deployment

Upload the folder to any static host such as GitHub Pages, Netlify, Vercel, or a University personal web directory. No build step is required.

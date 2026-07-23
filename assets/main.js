
const data = window.siteData || {};
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function setActiveNav() {
  const path = window.location.pathname.split('/').pop() || 'index.html';
  $$('.site-nav a').forEach(a => {
    if (a.getAttribute('href') === path) a.setAttribute('aria-current', 'page');
  });
}

function initNav() {
  const btn = $('.nav-toggle');
  const nav = $('#site-nav');
  if (!btn || !nav) return;
  const close = () => {
    nav.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
  };
  btn.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', String(open));
  });
  nav.addEventListener('click', e => {
    if (e.target.closest('a')) close();
  });
  document.addEventListener('click', e => {
    if (!nav.classList.contains('open')) return;
    if (!nav.contains(e.target) && !btn.contains(e.target)) close();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') close();
  });
}

function escapeHTML(str = '') {
  return String(str).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

function formatMultilineHTML(str = '') {
  return escapeHTML(str).replace(/\r?\n/g, '<br>');
}

function fillProfile() {
  const p = data.profile || {};
  $$('[data-profile]').forEach(el => {
    const key = el.dataset.profile;
    if (key === 'portrait') { el.src = p.portrait || ''; return; }
    el.textContent = p[key] || '';
  });
  $$('[data-research-areas]').forEach(el => {
    el.innerHTML = (p.researchAreas || []).map(area => `<span class="chip">${escapeHTML(area)}</span>`).join('');
  });
  $$('[data-link-list="footer"]').forEach(el => {
    const internal = [{ label: 'Research Radar', url: 'research-radar.html' }, { label: 'Essays', url: 'writing.html' }];
    const allowed = (p.links || []).filter(l => ['University profile','Google Scholar','ORCID','LinkedIn','Futures of Science blog'].includes(l.label));
    const internalLinks = internal.map(l => `<a href="${l.url}">${escapeHTML(l.label)}</a>`).join('');
    const externalLinks = allowed.map(l => `<a href="${l.url}" target="_blank" rel="noreferrer">${escapeHTML(l.label)}</a>`).join('');
    el.innerHTML = internalLinks + externalLinks;
  });
}

function pubCategoryClass(category) {
  if (category.includes('Peer')) return 'peer';
  if (category.includes('books')) return 'book';
  if (category.includes('Professional')) return 'professional';
  return 'other';
}

function publicationGroupHeading(category) {
  const descriptions = {
    'Peer-reviewed scientific articles': 'Peer-reviewed work in futures studies, philosophy of science, and historiography.',
    'Scientific books and edited volumes': 'Monographs, edited books, and special issues.',
    'Non-refereed scientific articles and reviews': 'Essay reviews, book reviews, and scholarly discussion pieces.',
    'Professional and stakeholder publications': 'Reports, policy briefs, and work written for decision-making contexts.'
  };
  return `<header class="publication-group-head"><h2>${escapeHTML(category)}</h2><p>${escapeHTML(descriptions[category] || '')}</p></header>`;
}

function isAcademicPublication(pub) {
  return pub.category.includes('Peer-reviewed') || pub.category.includes('Scientific books') || pub.category.includes('Non-refereed scientific');
}

function renderPublicationGroups(publications) {
  const groups = [...new Set(publications.map(p => p.category))];
  return groups.map(category => {
    const items = publications.filter(p => p.category === category).map(p => publicationCard(p)).join('');
    return `<section class="publication-group">${publicationGroupHeading(category)}${items}</section>`;
  }).join('');
}

function renderPublicFacingBlock() {
  const updates = ((data.engagement && data.engagement.updates) || []).slice(0, 5);
  if (!updates.length) return '';
  const cards = updates.map(item => `<article class="public-item">
    <div class="public-kind">${escapeHTML(item.kind)} · ${escapeHTML(item.date)}</div>
    <h3>${escapeHTML(item.title)}</h3>
    <p>${escapeHTML(item.text)}</p>
    <a class="tiny-link" href="${item.url}" target="_blank" rel="noreferrer">Open link</a>
  </article>`).join('');
  return `<section class="publication-group public-facing-group">
    <header class="publication-group-head"><h2>Public writing and updates</h2><p>Blog, LinkedIn, and university pieces.</p></header>
    ${cards}
  </section>`;
}

function renderPublicationBoard(publications, includePublicFacing = false) {
  const academic = publications.filter(isAcademicPublication);
  const professional = publications.filter(p => !isAcademicPublication(p));
  const academicCount = academic.length;
  const publicCount = professional.length + (includePublicFacing ? (((data.engagement && data.engagement.updates) || []).slice(0, 5).length) : 0);
  return `<div class="publication-board">
    <section class="publication-column academic-column">
      <header class="column-head">
        <p class="eyebrow">Academic</p>
        <h2>Research publications</h2>
        <p>Peer-reviewed articles, books, chapters, and reviews</p>
      </header>
      ${renderPublicationGroups(academic) || '<p>No matching academic items.</p>'}
    </section>
    <aside class="publication-column public-column">
      <header class="column-head">
        <p class="eyebrow">Professional / societal</p>
        <h2>Reports, briefs, engagement</h2>
        <p>Reports, briefs, and public-facing research work</p>
      </header>
      ${renderPublicationGroups(professional) || '<p>No matching professional items.</p>'}
      ${includePublicFacing ? renderPublicFacingBlock() : ''}
    </aside>
  </div>`;
}

function publicationCard(pub, compact = false) {
  const links = (pub.links || []).map(l => `<a class="tiny-link" href="${l.url}" target="_blank" rel="noreferrer">${escapeHTML(l.label)}</a>`).join('');
  const tags = (pub.tags || []).map(t => `<span class="pub-tag">${escapeHTML(t)}</span>`).join('');
  const citation = `${pub.authors} (${pub.year}). ${pub.title}. ${pub.venue}.`;
  if (compact) {
    return `<article class="card">
      <div class="meta">${escapeHTML(pub.year)} · ${escapeHTML(pub.type)}</div>
      <h3>${escapeHTML(pub.title)}</h3>
      <p>${escapeHTML(pub.venue)}</p>
      <div class="card-actions">${links || ''}<button class="copy-button" data-copy="${escapeHTML(citation)}">Copy citation</button></div>
    </article>`;
  }
  return `<article class="pub-card" data-category="${escapeHTML(pub.category)}">
    <div class="pub-year">${escapeHTML(pub.year)}</div>
    <div>
      <span class="pub-category ${pubCategoryClass(pub.category)}">${escapeHTML(pub.category)}</span>
      <h3>${escapeHTML(pub.title)}</h3>
      <div class="pub-meta">${escapeHTML(pub.authors)}</div>
      <p><strong>${escapeHTML(pub.type)}</strong> · ${escapeHTML(pub.venue)}${pub.status ? ` · ${escapeHTML(pub.status)}` : ''}</p>
      <div class="pub-tags">${tags}</div>
      <div class="pub-links">${links}<button class="copy-button" data-copy="${escapeHTML(citation)}">Copy citation</button></div>
    </div>
  </article>`;
}

function initCopyButtons(root = document) {
  $$('[data-copy]', root).forEach(btn => {
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.copy || '');
        const original = btn.textContent;
        btn.textContent = 'Copied';
        setTimeout(() => btn.textContent = original, 1300);
      } catch (e) {
        btn.textContent = 'Select citation';
      }
    });
  });
}

function renderStats() {
  const el = $('[data-stats]');
  if (!el) return;
  el.innerHTML = [
    ['Peer-reviewed arguments', 'Research in futures studies, philosophy of science, historiography, and counterfactual thinking.'],
    ['Books and frameworks', 'Long-form work where concepts and methods have room to develop.'],
    ['Research-grounded scans', 'Horizon scanning based on substantial bodies of papers, books, and reports.'],
    ['Methods that connect fields', 'Dialectic Delphi, narratives-with-branches, CLA extensions, and futures as space.']
  ].map(([title, text]) => `<div class="stat nature-card"><strong>${title}</strong><span>${text}</span></div>`).join('');
}

function renderSelectedPublications() {
  const el = $('[data-selected-publications]');
  if (!el) return;
  const titles = [
    'University futures: Insights from a dialectic Delphi study',
    'Futures of Work: A Framework to Understand the Directions of Change',
    'The Shining: Illuminating Philosophy and Futures Studies',
    'When We Work. Delphi Results on Time and Temporality within Futures of Work',
    'Time and Futures. Analysis of time-needs in futures research',
    'Causal Explanation in Historiography'
  ];
  const selected = titles.map(t => (data.publications || []).find(p => p.title === t)).filter(Boolean);
  el.innerHTML = selected.map(p => publicationCard(p, true)).join('');
  initCopyButtons(el);
}

function renderVision() {
  const v = data.vision || {};
  $$('[data-vision="headline"]').forEach(el => el.textContent = v.headline || '');
  $$('[data-vision="summary"]').forEach(el => el.textContent = v.summary || '');
  $$('[data-vision-pillars]').forEach(el => {
    el.innerHTML = (v.pillars || []).map(p => `<article class="mini-card"><h3>${escapeHTML(p.title)}</h3><p>${escapeHTML(p.text)}</p></article>`).join('');
  });
}

function engagementCard(item) {
  return `<article class="card">
    <div class="meta">${escapeHTML(item.kind)} · ${escapeHTML(item.date)}</div>
    <h3>${escapeHTML(item.title)}</h3>
    <p>${escapeHTML(item.text)}</p>
    <div class="card-actions"><a class="tiny-link" href="${item.url}" target="_blank" rel="noreferrer">Open link</a></div>
  </article>`;
}

function renderEngagement() {
  const items = (data.engagement && data.engagement.updates) || [];
  const preview = $('[data-engagement-preview]');
  if (preview) preview.innerHTML = items.slice(0, 3).map(engagementCard).join('');
  const list = $('[data-engagement-list]');
  if (list) list.innerHTML = items.map(engagementCard).join('');
  const pro = $('[data-professional-publications]');
  if (pro) {
    const pubs = (data.publications || []).filter(p => p.category.includes('Professional')).slice(0, 6);
    pro.innerHTML = pubs.map(p => publicationCard(p, true)).join('');
    initCopyButtons(pro);
  }
}

function initPublicationPage() {
  const list = $('[data-publication-list]');
  if (!list) return;
  const input = $('[data-publication-search]');
  const filtersEl = $('[data-publication-filters]');
  const countEl = $('[data-publication-count]');
  const pubs = data.publications || [];
  const categories = ['All', ...new Set(pubs.map(p => p.category))];
  let current = 'All';
  filtersEl.innerHTML = categories.map(cat => `<button class="filter-button" type="button" data-filter="${escapeHTML(cat)}" aria-pressed="${cat === current}">${escapeHTML(cat)}</button>`).join('');
  function render() {
    const q = (input.value || '').trim().toLowerCase();
    const filtered = pubs.filter(p => {
      const hay = [p.category, p.type, p.year, p.title, p.authors, p.venue, p.status, ...(p.tags || [])].join(' ').toLowerCase();
      return (current === 'All' || p.category === current) && (!q || hay.includes(q));
    });
    const academicCount = filtered.filter(isAcademicPublication).length;
    const otherCount = filtered.length - academicCount;
    countEl.textContent = current === 'All'
      ? 'Showing scholarly publications, books, reviews, reports, and stakeholder-oriented work.'
      : 'Filtered selection shown.';
    list.innerHTML = renderPublicationBoard(filtered, !q && current === 'All');
    initCopyButtons(list);
  }
  filtersEl.addEventListener('click', e => {
    const btn = e.target.closest('[data-filter]');
    if (!btn) return;
    current = btn.dataset.filter;
    $$('.filter-button', filtersEl).forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
    render();
  });
  input.addEventListener('input', render);
  render();
}

function renderTimelineItem(item) {
  const details = item.details ? `<ul>${item.details.map(d => `<li>${escapeHTML(d)}</li>`).join('')}</ul>` : '';
  const title = item.role || item.degree || item.item || '';
  const subtitle = item.institution ? `<p>${escapeHTML(item.institution)}</p>` : '';
  const date = item.period || item.year || '';
  return `<article class="timeline-item"><div class="timeline-date">${escapeHTML(date)}</div><div><h3>${escapeHTML(title)}</h3>${subtitle}${details}</div></article>`;
}

function renderCV() {
  $$('[data-cv]').forEach(el => {
    const key = el.dataset.cv;
    const arr = (data.cv && data.cv[key]) || [];
    el.innerHTML = arr.map(renderTimelineItem).join('');
  });
}

async function renderRadarWisdom() {
  const list = $('[data-radar-wisdom]');
  if (!list) return;
  try {
    const res = await fetch('assets/radar-wisdom.json', { cache: 'no-store' });
    if (!res.ok) throw new Error('Could not load wisdom data');
    const payload = await res.json();
    const items = Array.isArray(payload.items) && payload.items.length
      ? payload.items
      : (payload.current ? [payload.current] : []);
    if (!items.length) return;

    list.innerHTML = items.map(item => {
      const tags = (item.tags || []).map(tag => `<span class="chip">${escapeHTML(tag)}</span>`).join('');
      const referenceParts = Array.isArray(item.referenceParts) ? item.referenceParts : [];
      const reference = item.reference || [item.creator, item.title, item.year].filter(Boolean).join(', ');
      const referenceHTML = referenceParts.length
        ? referenceParts.map(part => part.italic
          ? `<em>${escapeHTML(part.text || '')}</em>`
          : escapeHTML(part.text || '')).join('')
        : escapeHTML(reference);
      const questions = Array.isArray(item.questions) ? item.questions : [];
      const emphasis = item.emphasis || '';
      const commentTitle = item.commentTitle ? `<p class="radar-wisdom-comment-title">${escapeHTML(item.commentTitle)}</p>` : '';
      const comment = item.comment ? `<p class="radar-wisdom-comment">${escapeHTML(item.comment)}</p>` : '';
      const questionLine = questions.length
        ? `<p class="radar-wisdom-questions">${questions.map(q => q === emphasis ? `<strong>${escapeHTML(q)}</strong>` : escapeHTML(q)).join(' ')}</p>`
        : '';

      return `<article class="radar-wisdom-card">
        <p class="radar-wisdom-quote">“${formatMultilineHTML(item.quote || '')}”</p>
        <p class="radar-wisdom-ref">${referenceHTML}</p>
        ${commentTitle}
        ${comment}
        ${questionLine}
        ${tags ? `<div class="radar-tags">${tags}</div>` : ''}
      </article>`;
    }).join('');
  } catch (err) {
    // Keep the static fallback cards in the HTML if the data file fails to load.
  }
}

async function renderResearchRadar() {
  const list = $('[data-radar-list]');
  if (!list) return;
  const countEl = $('[data-radar-count]');
  try {
    const res = await fetch('assets/research-radar-approved.json', { cache: 'no-store' });
    if (!res.ok) throw new Error('Could not load radar data');
    const payload = await res.json();
    const items = Array.isArray(payload.items) ? payload.items : [];
    if (countEl) countEl.textContent = `${items.length} selected references`;
    const topics = [...new Set(items.map(item => item.topic || 'Other'))];
    list.innerHTML = topics.map(topic => {
      const cards = items.filter(item => (item.topic || 'Other') === topic).map(item => {
        const connects = (item.connectsWith || []).map(tag => `<span class="chip">${escapeHTML(tag)}</span>`).join('');
        return `<article class="radar-item">
          <div class="radar-meta">${escapeHTML(item.authors || '')} · ${escapeHTML(item.year || '')}</div>
          <h3>${escapeHTML(item.title || '')}</h3>
          <p class="radar-source">${escapeHTML(item.source || '')}</p>
          <p>${escapeHTML(item.why || '')}</p>
          ${connects ? `<div class="radar-tags">${connects}</div>` : ''}
        </article>`;
      }).join('');
      return `<section class="radar-topic"><h2>${escapeHTML(topic)}</h2><div class="radar-topic-grid">${cards}</div></section>`;
    }).join('');
  } catch (err) {
    list.innerHTML = '<p>The Research Radar data could not be loaded.</p>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  setActiveNav();
  fillProfile();
  renderStats();
  renderSelectedPublications();
  renderVision();
  renderEngagement();
  initPublicationPage();
  renderCV();
  renderRadarWisdom();
  renderResearchRadar();
});

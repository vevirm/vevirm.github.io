
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
  btn.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', String(open));
  });
}

function escapeHTML(str = '') {
  return String(str).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
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
    const allowed = (p.links || []).filter(l => ['University profile','Google Scholar','ORCID','LinkedIn','Futures of Science blog'].includes(l.label));
    el.innerHTML = allowed.map(l => `<a href="${l.url}" target="_blank" rel="noreferrer">${escapeHTML(l.label)}</a>`).join('');
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
    'Peer-reviewed scientific articles': 'Journal articles and peer-reviewed chapters.',
    'Scientific books and edited volumes': 'Authored books, edited volumes, and special issues.',
    'Non-refereed scientific articles and reviews': 'Essay reviews, book reviews, and scientific discussion pieces.',
    'Professional and stakeholder publications': 'Reports, policy briefs, and stakeholder-facing texts.'
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
    <header class="publication-group-head"><h2>Public writing and updates</h2><p>LinkedIn, blog, and university pieces.</p></header>
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
        <p class="eyebrow">Academic work</p>
        <h2>Research publications</h2>
        <p>${academicCount} items</p>
      </header>
      ${renderPublicationGroups(academic) || '<p>No matching academic items.</p>'}
    </section>
    <aside class="publication-column public-column">
      <header class="column-head">
        <p class="eyebrow">Beyond academia</p>
        <h2>Reports, briefs, and engagement</h2>
        <p>${publicCount} items</p>
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
      <h2>${escapeHTML(pub.title)}</h2>
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
  const pubs = data.publications || [];
  const peer = pubs.filter(p => p.category.includes('Peer')).length;
  const books = pubs.filter(p => p.category.includes('books')).length;
  const professional = pubs.filter(p => p.category.includes('Professional')).length;
  el.innerHTML = [
    [pubs.length, 'listed outputs'],
    [peer, 'peer-reviewed / academic articles & chapters'],
    [books, 'books & edited volumes'],
    [professional, 'professional / stakeholder publications']
  ].map(([n, label]) => `<div class="stat"><strong>${n}</strong><span>${label}</span></div>`).join('');
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
      ? `${academicCount} academic items · ${otherCount} professional/stakeholder items`
      : `${filtered.length} item${filtered.length === 1 ? '' : 's'} shown`;
    const showBoard = current === 'All';
    list.innerHTML = showBoard ? renderPublicationBoard(filtered, !q) : filtered.map(p => publicationCard(p)).join('');
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
});

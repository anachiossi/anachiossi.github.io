/**
 * films.js — Phase 1 + Phase 2 + Phase 3
 *
 * Phase 1: data loading · grid rendering · search
 * Phase 2: modal · prev/next navigation · keyboard · swipe
 * Phase 3: awards badge · festivals badge · box office
 */

'use strict';

// ── State ─────────────────────────────────────────────────────────────────────
let allProjects      = [];
let currentProjects  = []; // modal reads this for prev/next navigation
let currentModalIndex = -1;
let isTransitioning  = false; // guard against rapid nav clicks

// ── Language display map ──────────────────────────────────────────────────────
const LANG_LABELS = {
  PT_BR: 'Portuguese (BR)', PT_PT: 'Portuguese (PT)',
  IT: 'Italian',  EN: 'English',  ES: 'Spanish',
  FR: 'French',   DE: 'German',   JA: 'Japanese',
  ZH: 'Chinese',  AR: 'Arabic',   RU: 'Russian',
};

// ── DOM refs — grid ───────────────────────────────────────────────────────────
const gridEl       = document.getElementById('films-grid');
const loadingEl    = document.getElementById('films-loading');
const errorEl      = document.getElementById('films-error');
const noResultsEl  = document.getElementById('films-no-results');
const searchEl     = document.getElementById('films-search');

// ── DOM refs — modal ──────────────────────────────────────────────────────────
const backdropEl      = document.getElementById('film-modal-backdrop');
const modalEl         = document.getElementById('film-modal');
const modalCloseEl    = document.getElementById('modal-close');
const modalPrevEl     = document.getElementById('modal-prev');
const modalNextEl     = document.getElementById('modal-next');
const modalScrollerEl = document.getElementById('modal-scroller');
const modalContentEl  = document.getElementById('modal-content');

// ── Utilities ─────────────────────────────────────────────────────────────────

function normalizeStr(str) {
  return str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

// Escape HTML for safe innerHTML insertion
function esc(val) {
  return String(val ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function sortByYear(projects) {
  return [...projects].sort((a, b) => {
    const aUp = a.release_status === 'upcoming';
    const bUp = b.release_status === 'upcoming';
    if (aUp && !bUp) return -1;
    if (bUp && !aUp) return  1;
    // Both upcoming or both released — descending year (0 falls to bottom)
    const ay = a.release_year || 0;
    const by = b.release_year || 0;
    if (ay === 0 && by !== 0) return  1;
    if (by === 0 && ay !== 0) return -1;
    return by - ay;
  });
}

function filterProjects(query) {
  if (!query.trim()) return allProjects;
  const q = normalizeStr(query.trim());
  return allProjects.filter(p => {
    const haystack = [
      p.title, p.director, p.role, p.type,
      ...(p.platforms     || []),
      ...(p.prod_country  || []),
      ...(p.prod_co       || []),
      ...(p.film_language || []),
    ].filter(Boolean).join(' ');
    return normalizeStr(haystack).includes(q);
  });
}

function yearLabel(project) {
  if (project.release_year > 0) return String(project.release_year);
  if (project.release_status === 'upcoming') return 'Upcoming';
  return '';
}

// ── Phase 1: card builder ─────────────────────────────────────────────────────

function createPlaceholder() {
  const div = document.createElement('div');
  div.className = 'film-card-placeholder';
  return div;
}

function buildCard(project, index) {
  const card = document.createElement('div');
  card.className = 'film-card';
  card.dataset.index = index;

  if (project.image_missing) {
    card.appendChild(createPlaceholder());
  } else {
    const img = document.createElement('img');
    img.src      = `assets/images/thumbs/${project.thumb_id || project.image_id}-thumb.avif`;
    img.alt      = project.title;
    img.loading  = 'lazy';
    img.decoding = 'async';
    img.onerror  = () => img.replaceWith(createPlaceholder());
    card.appendChild(img);
  }

  const overlay = document.createElement('div');
  overlay.className = 'film-card-overlay';
  overlay.innerHTML =
    `<div class="film-card-overlay-text">` +
      `<span class="film-card-overlay-title">${esc(project.title)}</span>` +
      (yearLabel(project)
        ? `<span class="film-card-overlay-year">${esc(yearLabel(project))}</span>`
        : '') +
    `</div>`;
  card.appendChild(overlay);

  card.addEventListener('click', () => {
    if (window.umami) window.umami.track('Film Click', { title: project.title });
    openModal(index);
  });

  return card;
}

// ── Phase 1: grid render ──────────────────────────────────────────────────────

function renderGrid(projects) {
  currentProjects = projects;
  gridEl.innerHTML = '';

  if (projects.length === 0) {
    gridEl.hidden      = true;
    noResultsEl.hidden = false;
    noResultsEl.textContent =
      `No projects found for "${searchEl.value}" — try a different search`;
    return;
  }

  noResultsEl.hidden = true;
  gridEl.hidden      = false;

  const fragment = document.createDocumentFragment();
  projects.forEach((p, i) => fragment.appendChild(buildCard(p, i)));
  gridEl.appendChild(fragment);
}

// ── Phase 2: modal content ────────────────────────────────────────────────────

function populateModal(project) {
  // ── Subtitle: year · type · first production country ──
  const subtitleParts = [
    yearLabel(project),
    project.type,
    project.prod_country && project.prod_country.length ? project.prod_country[0] : null,
  ].filter(Boolean);
  const subtitleHtml = subtitleParts.length
    ? `<p class="modal-subtitle">${esc(subtitleParts.join(' · '))}</p>`
    : '';

  // ── Coin badges (top-right of header, decorative) ──
  const coinParts = [];
  if (project.awards_count > 0) {
    coinParts.push(
      `<div class="modal-coin">` +
        `<img src="assets/images/badge_awards.png" alt="${esc(project.awards_count)} award${project.awards_count !== 1 ? 's' : ''}">` +
      `</div>`
    );
  }
  if (project.festivals_count > 0) {
    coinParts.push(
      `<div class="modal-coin">` +
        `<img src="assets/images/badge_festivals.png" alt="${esc(project.festivals_count)} festival${project.festivals_count !== 1 ? 's' : ''}">` +
      `</div>`
    );
  }
  const coinBadgesHtml = coinParts.length
    ? `<div class="modal-coins">${coinParts.join('')}</div>`
    : '';

  // ── Role · Department ──
  const roleParts = [project.role, project.department].filter(Boolean);
  const roleHtml = roleParts.length
    ? `<p class="modal-role">${esc(roleParts.join(' · '))}</p>`
    : '';

  // ── Description ──
  const descHtml = project.description
    ? `<p class="modal-desc">${esc(project.description)}</p>`
    : '';

  // ── Platforms ──
  let platformsHtml = '';
  if (project.platforms && project.platforms.length) {
    const pills = project.platforms
      .map(p => `<span class="modal-pill">${esc(p)}</span>`)
      .join('');
    platformsHtml =
      `<div class="modal-section">` +
        `<span class="modal-section-label">Available on</span>` +
        `<div class="modal-pills">${pills}</div>` +
      `</div>`;
  }

  // ── Detail rows (director, production, countries, languages) ──
  const details = [];
  if (project.director && project.director.length) {
    const dirs = Array.isArray(project.director) ? project.director : [project.director];
    details.push(['Director', esc(dirs.join(', '))]);
  }
  if (project.prod_co && project.prod_co.length) {
    details.push(['Production', esc(project.prod_co.join(', '))]);
  }
  if (project.prod_country && project.prod_country.length) {
    details.push(['Countries', esc(project.prod_country.join(', '))]);
  }
  if (project.film_language && project.film_language.length) {
    const langs = project.film_language
      .map(c => LANG_LABELS[c] || c)
      .join(', ');
    details.push(['Languages', esc(langs)]);
  }

  const detailsHtml = details.length
    ? `<div class="modal-details">` +
        details.map(([label, value]) =>
          `<div class="modal-detail-row">` +
            `<span class="modal-detail-label">${label}</span>` +
            `<span class="modal-detail-value">${value}</span>` +
          `</div>`
        ).join('') +
      `</div>`
    : '';

  // ── IMDb link ──
  const imdbHtml = project.imdb_link
    ? `<a class="modal-imdb" href="${esc(project.imdb_link)}" target="_blank" rel="noopener">` +
        `View on IMDb ↗` +
      `</a>`
    : '';

  // ── Awards expandable ──
  let awardsHtml = '';
  if (project.awards_count > 0 && project.awards_detail && project.awards_detail.length) {
    const items = project.awards_detail.map(a => {
      const isSoundAward = a.is_sound_award === true;
      const sub = [a.event, a.year, a.country].filter(Boolean).join(' · ');
      return `<li class="modal-badge-item${isSoundAward ? ' modal-badge-item--sound' : ''}">` +
        `<span class="modal-badge-item-main">${esc(a.category)} — ${esc(a.result)}</span>` +
        `<span class="modal-badge-item-sub">${esc(sub)}</span>` +
      `</li>`;
    }).join('');
    awardsHtml =
      `<div class="modal-badge modal-badge--awards" role="button" tabindex="0" aria-expanded="false">` +
        `<div class="modal-badge-header">` +
          `<span class="modal-badge-icon">🏆</span>` +
          `<span class="modal-badge-label">${esc(project.awards_count)} award${project.awards_count !== 1 ? 's' : ''}</span>` +
          `<svg class="modal-badge-chevron" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>` +
        `</div>` +
        `<div class="modal-badge-body">` +
          `<ul class="modal-badge-list">${items}</ul>` +
        `</div>` +
      `</div>`;
  }

  // ── Festivals expandable ──
  let festivalsHtml = '';
  if (project.festivals_count > 0 && project.festivals_detail && project.festivals_detail.length) {
    const items = project.festivals_detail.map(f => {
      const sub = [f.year, f.country].filter(Boolean).join(' · ');
      return `<li class="modal-badge-item">` +
        `<span class="modal-badge-item-main">${esc(f.name)}</span>` +
        `<span class="modal-badge-item-sub">${esc(sub)}</span>` +
      `</li>`;
    }).join('');
    festivalsHtml =
      `<div class="modal-badge modal-badge--festivals" role="button" tabindex="0" aria-expanded="false">` +
        `<div class="modal-badge-header">` +
          `<span class="modal-badge-icon">★</span>` +
          `<span class="modal-badge-label">${esc(project.festivals_count)} festival${project.festivals_count !== 1 ? 's' : ''}</span>` +
          `<svg class="modal-badge-chevron" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>` +
        `</div>` +
        `<div class="modal-badge-body">` +
          `<ul class="modal-badge-list">${items}</ul>` +
        `</div>` +
      `</div>`;
  }

  const badgesHtml = (awardsHtml || festivalsHtml)
    ? `<div class="modal-badges">${awardsHtml}${festivalsHtml}</div>`
    : '';

  // ── Assemble — no hero image ──
  modalContentEl.innerHTML =
    `<div class="modal-body">` +
      `<div class="modal-header">` +
        `<div class="modal-header-main">` +
          `<h2 class="modal-title">${esc(project.title)}</h2>` +
          subtitleHtml +
        `</div>` +
        coinBadgesHtml +
      `</div>` +
      roleHtml +
      descHtml +
      platformsHtml +
      detailsHtml +
      imdbHtml +
      badgesHtml +
    `</div>`;

  // Badge expand/collapse
  modalContentEl.querySelectorAll('.modal-badge').forEach(badge => {
    const toggle = () => {
      const open = badge.classList.toggle('is-open');
      badge.setAttribute('aria-expanded', open ? 'true' : 'false');
    };
    badge.addEventListener('click', toggle);
    badge.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    });
  });

  // Update ARIA label on dialog
  modalEl.setAttribute('aria-label', project.title);
}

// ── Phase 2: open / close / navigate ─────────────────────────────────────────

function updateNavButtons() {
  modalPrevEl.hidden = currentModalIndex <= 0;
  modalNextEl.hidden = currentModalIndex >= currentProjects.length - 1;
}

function openModal(index) {
  currentModalIndex = index;
  populateModal(currentProjects[index]);
  updateNavButtons();
  backdropEl.classList.add('is-open');
  backdropEl.removeAttribute('aria-hidden');
  document.body.style.overflow = 'hidden';
  // Focus close button for keyboard users
  requestAnimationFrame(() => modalCloseEl.focus());
}

function closeModal() {
  backdropEl.classList.remove('is-open');
  backdropEl.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
  currentModalIndex = -1;
}

function navigateTo(newIndex) {
  if (isTransitioning) return;
  if (newIndex < 0 || newIndex >= currentProjects.length) return;
  isTransitioning = true;
  modalContentEl.classList.add('is-fading');
  modalScrollerEl.scrollTop = 0;
  setTimeout(() => {
    currentModalIndex = newIndex;
    populateModal(currentProjects[newIndex]);
    updateNavButtons();
    modalContentEl.classList.remove('is-fading');
    isTransitioning = false;
  }, 140);
}

// ── Phase 2: event listeners ──────────────────────────────────────────────────

modalCloseEl.addEventListener('click', closeModal);

// Backdrop click — close only when clicking the dark area, not the modal box
backdropEl.addEventListener('click', e => {
  if (e.target === backdropEl) closeModal();
});

modalPrevEl.addEventListener('click', () => navigateTo(currentModalIndex - 1));
modalNextEl.addEventListener('click', () => navigateTo(currentModalIndex + 1));

// Keyboard: ESC close · arrow keys navigate · Tab trap focus within modal
document.addEventListener('keydown', e => {
  if (!backdropEl.classList.contains('is-open')) return;

  if (e.key === 'Escape') {
    closeModal();
    return;
  }
  if (e.key === 'ArrowLeft')  { navigateTo(currentModalIndex - 1); return; }
  if (e.key === 'ArrowRight') { navigateTo(currentModalIndex + 1); return; }

  // Basic focus trap
  if (e.key === 'Tab') {
    const focusable = Array.from(
      modalEl.querySelectorAll('button:not([hidden]), a[href]')
    );
    if (!focusable.length) return;
    const first = focusable[0];
    const last  = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
});

// Touch swipe — horizontal swipe on the scroller navigates; vertical scrolls normally
let touchStartX = 0;
let touchStartY = 0;

modalScrollerEl.addEventListener('touchstart', e => {
  touchStartX = e.touches[0].clientX;
  touchStartY = e.touches[0].clientY;
}, { passive: true });

modalScrollerEl.addEventListener('touchend', e => {
  const dx = e.changedTouches[0].clientX - touchStartX;
  const dy = e.changedTouches[0].clientY - touchStartY;
  // Treat as horizontal swipe only when dx dominates and exceeds 50px
  if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50) {
    if (dx < 0) navigateTo(currentModalIndex + 1); // swipe left  → next
    else        navigateTo(currentModalIndex - 1); // swipe right → prev
  }
}, { passive: true });

// ── Bootstrap ─────────────────────────────────────────────────────────────────

async function init() {
  try {
    const res = await fetch('assets/films.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    allProjects      = sortByYear(data);
    loadingEl.hidden = true;
    renderGrid(allProjects);

    let searchTrackTimer;
    searchEl.addEventListener('input', () => {
      renderGrid(filterProjects(searchEl.value));
      clearTimeout(searchTrackTimer);
      searchTrackTimer = setTimeout(() => {
        if (searchEl.value.trim() && window.umami) {
          window.umami.track('Film Search', { query: searchEl.value.trim() });
        }
      }, 500);
    });

  } catch (err) {
    loadingEl.hidden    = true;
    errorEl.hidden      = false;
    errorEl.textContent = 'Could not load projects. Please refresh the page.';
    console.error('[films] fetch error:', err);
  }
}

init();

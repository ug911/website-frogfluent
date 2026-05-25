// Loads tutor data fetched from the Wise API at build time and renders cards
// across the site. Wires up "Book a Trial" and "Buy a Session" buttons.
(async function () {
  const grids = document.querySelectorAll('[data-tutor-grid]');
  if (!grids.length) return;

  let tutors = [];
  try {
    const res = await fetch('assets/tutors-data.json', { cache: 'no-cache' });
    tutors = await res.json();
  } catch (e) {
    grids.forEach(g => (g.innerHTML = '<p class="loading">Could not load tutors. Please try again later.</p>'));
    return;
  }

  function escape(s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function teaser(bio, n = 180) {
    if (!bio) return '';
    const cleaned = bio.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    if (cleaned.length <= n) return cleaned;
    return cleaned.slice(0, n).replace(/\s+\S*$/, '') + '…';
  }

  function priceLabel(p) {
    if (!p || !p.value) return 'Free trial';
    const sym = p.currency === 'USD' ? '$' : (p.currency || '') + ' ';
    return `${sym}${p.value}`;
  }

  function cardHTML(t, idx) {
    const tagline = t.tagline || `Teaches ${t.language}`;
    const photo = t.photo || 'assets/tutors/tutor1.jpg';
    const detail = `tutor-details.html?id=${encodeURIComponent(t.class_id)}`;
    return `
      <article class="tutor-card">
        <a class="tutor-photo" href="${detail}"><img src="${escape(photo)}" alt="${escape(t.name)}" loading="lazy"/></a>
        <div class="tutor-body">
          <div class="rating">★ 4.9/5 · <span class="price">${priceLabel(t.price)} / session</span></div>
          <h3><a href="${detail}">${escape(t.name)}</a></h3>
          <p class="meta">${escape(t.country)} · Teaches ${escape(t.language)}</p>
          <p>${escape(teaser(tagline, 140))}</p>
          <div class="card-actions">
            <button class="btn btn-outline btn-sm" data-action="trial" data-idx="${idx}">Book a Trial</button>
            <a class="btn btn-primary btn-sm" href="${detail}">View profile</a>
          </div>
        </div>
      </article>
    `;
  }

  grids.forEach(grid => {
    const limit = parseInt(grid.dataset.limit || '0', 10);
    const list = limit > 0 ? tutors.slice(0, limit) : tutors;
    grid.innerHTML = list.map((t, i) => cardHTML(t, tutors.indexOf(t))).join('');
  });

  // Modal
  const modal = document.createElement('div');
  modal.className = 'wise-modal';
  modal.innerHTML = `
    <div class="wise-modal-backdrop" data-close></div>
    <div class="wise-modal-body">
      <button class="wise-modal-close" data-close aria-label="Close">×</button>
      <div class="wise-modal-content"></div>
    </div>
  `;
  document.body.appendChild(modal);
  const content = modal.querySelector('.wise-modal-content');
  modal.addEventListener('click', e => {
    if (e.target.matches('[data-close]')) modal.classList.remove('open');
  });

  function openTrialModal(t) {
    if (typeof window.openBookingWidget === 'function') {
      window.openBookingWidget(t);
    } else {
      alert('Booking widget not loaded.');
    }
  }

  function openBuyModal(t) {
    content.innerHTML = `
      <div class="wise-modal-head">
        <img src="${escape(t.photo)}" alt=""/>
        <div>
          <h3>${escape(t.title || ('1:1 with ' + t.name))}</h3>
          <p>${priceLabel(t.price)} · Single session</p>
        </div>
      </div>
      <ul class="check-list small">
        ${(t.highlights || []).map(h => `<li>${escape(h)}</li>`).join('')}
      </ul>
      <p>Payment is processed securely by Wise. Sign in (or create an account) to complete checkout.</p>
      <div class="wise-modal-actions">
        <button class="btn btn-ghost" data-close>Cancel</button>
        <a href="${escape(t.course_link)}" target="_blank" rel="noopener" class="btn btn-primary">Continue to checkout →</a>
      </div>
    `;
    modal.classList.add('open');
  }

  document.addEventListener('click', e => {
    const btn = e.target.closest('button[data-action]');
    if (!btn) return;
    const idx = parseInt(btn.dataset.idx, 10);
    const t = tutors[idx];
    if (!t) return;
    if (btn.dataset.action === 'trial') openTrialModal(t);
    if (btn.dataset.action === 'buy') openBuyModal(t);
  });
})();

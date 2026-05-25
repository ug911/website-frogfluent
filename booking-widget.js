// Native inline booking widget for the Wise demoRoom flow.
// Calls /public/demoRooms (slot lookup) + /public/demoRooms/{id}/session (book)
// so we don't have to iframe the Wise page (which fails on third-party cookies).
(function () {
  const API = 'https://api.wiseapp.live';
  const NAMESPACE = 'frogfluent-sample';
  const HEADERS = {
    'x-wise-namespace': NAMESPACE,
    'x-api-key': 'web:aff7589260fd9f8ba437674d25225728',
  };
  const TZ = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata';

  function esc(s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function fmtMonth(d) { return pad(d.getMonth() + 1) + '-' + d.getFullYear(); }
  function fmtTime(d) {
    return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  }
  function fmtDay(d) {
    return d.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' });
  }
  function sameDay(a, b) {
    return a.getFullYear() === b.getFullYear() &&
           a.getMonth() === b.getMonth() &&
           a.getDate() === b.getDate();
  }

  async function fetchSlots(slug, month, duration) {
    const u = new URL(API + '/public/demoRooms');
    u.searchParams.set('slug', slug);
    u.searchParams.set('month', month);
    u.searchParams.set('duration', String(duration));
    u.searchParams.set('showRegistrationForm', 'true');
    const r = await fetch(u, { headers: HEADERS });
    const json = await r.json();
    if (json.status !== 200) throw new Error(json.message || 'Failed to load slots');
    return json.data;
  }

  async function bookSession(demoRoomId, payload) {
    const r = await fetch(`${API}/public/demoRooms/${demoRoomId}/session`, {
      method: 'POST',
      headers: { ...HEADERS, 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const json = await r.json();
    if (json.status !== 200) throw new Error(json.message || 'Booking failed');
    return json.data;
  }

  function ensureModal() {
    let modal = document.getElementById('wise-bw-modal');
    if (modal) return modal;
    modal = document.createElement('div');
    modal.id = 'wise-bw-modal';
    modal.className = 'wise-modal';
    modal.innerHTML = `
      <div class="wise-modal-backdrop" data-close></div>
      <div class="wise-modal-body wide">
        <button class="wise-modal-close" data-close aria-label="Close">×</button>
        <div class="wise-modal-content"></div>
      </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', e => {
      if (e.target.matches('[data-close]')) modal.classList.remove('open');
    });
    return modal;
  }

  window.openBookingWidget = async function (tutor) {
    const modal = ensureModal();
    const content = modal.querySelector('.wise-modal-content');
    const slug = tutor.demo_slug || (tutor.consultation_booking_link || '').split('/book/').pop();
    if (!slug) {
      alert('No trial booking link is configured for this tutor.');
      return;
    }

    const state = {
      duration: 30,
      monthDate: new Date(),
      selected: null,         // { startISO, endISO, dateObj }
      data: null,             // full /public/demoRooms response
      slotsByDay: new Map(),  // Map<YYYY-MM-DD, [{startDate,endDate}]>
      form: { name: '', email: '' },
    };

    function head() {
      return `
        <div class="bw-head">
          <img src="${esc(tutor.photo)}" alt=""/>
          <div>
            <h3>Book a Trial with ${esc(tutor.name)}</h3>
            <p>${state.duration}-minute trial · times in ${esc(TZ)}</p>
          </div>
        </div>`;
    }

    function renderLoading() {
      content.innerHTML = `${head()}<div class="bw-loading"><div class="bw-spinner"></div><p>Loading availability…</p></div>`;
    }

    function renderError(msg) {
      content.innerHTML = `
        ${head()}
        <div class="bw-error">
          <p>${esc(msg)}</p>
          <a href="${esc(tutor.consultation_booking_link)}" target="_blank" rel="noopener" class="btn btn-outline btn-sm">Open Wise scheduler in a new tab</a>
        </div>`;
    }

    async function load() {
      renderLoading();
      try {
        state.data = await fetchSlots(slug, fmtMonth(state.monthDate), state.duration);
      } catch (e) {
        renderError(e.message || 'Could not load slots');
        return;
      }
      // Map slots into local-day buckets
      state.slotsByDay = new Map();
      const sd = state.data.slotDetails;
      const tsStart = new Date(sd.tsStart);
      const slotDur = sd.slotDurationInSeconds * 1000;
      for (const s of sd.availableSlots || []) {
        const start = new Date(tsStart.getTime() + s.d * 1000);
        const end = new Date(start.getTime() + slotDur);
        const key = start.getFullYear() + '-' + pad(start.getMonth() + 1) + '-' + pad(start.getDate());
        if (!state.slotsByDay.has(key)) state.slotsByDay.set(key, []);
        state.slotsByDay.get(key).push({ start, end });
      }
      renderPicker();
    }

    function renderPicker() {
      const m = state.monthDate;
      const monthLabel = m.toLocaleDateString([], { month: 'long', year: 'numeric' });
      const firstOfMonth = new Date(m.getFullYear(), m.getMonth(), 1);
      const daysInMonth = new Date(m.getFullYear(), m.getMonth() + 1, 0).getDate();
      const startWeekday = firstOfMonth.getDay();
      const today = new Date(); today.setHours(0,0,0,0);

      let cells = '';
      // Day-of-week header
      for (const d of ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']) cells += `<div class="bw-dow">${d}</div>`;
      // Leading empty cells
      for (let i = 0; i < startWeekday; i++) cells += `<div class="bw-empty"></div>`;
      for (let day = 1; day <= daysInMonth; day++) {
        const d = new Date(m.getFullYear(), m.getMonth(), day);
        const key = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
        const slots = state.slotsByDay.get(key) || [];
        const past = d < today;
        const has = slots.length > 0;
        const isSel = state.selected && sameDay(state.selected.dateObj, d);
        const cls = ['bw-day'];
        if (past) cls.push('past');
        else if (!has) cls.push('empty');
        else cls.push('avail');
        if (isSel) cls.push('selected');
        cells += `<button class="${cls.join(' ')}" ${past || !has ? 'disabled' : ''} data-day="${key}">${day}</button>`;
      }

      const slotsForDay = state.selected
        ? (state.slotsByDay.get(state.selected.dayKey) || [])
        : null;

      content.innerHTML = `
        ${head()}
        <div class="bw-controls">
          <div class="bw-month-nav">
            <button class="bw-icon" data-month="-1" aria-label="Previous">‹</button>
            <span>${monthLabel}</span>
            <button class="bw-icon" data-month="1" aria-label="Next">›</button>
          </div>
          <div class="bw-duration">
            ${(state.data.demoRoom.durations || [30]).map(d =>
              `<button class="bw-pill ${d === state.duration ? 'active' : ''}" data-dur="${d}">${d} min</button>`
            ).join('')}
          </div>
        </div>
        <div class="bw-grid">
          <div class="bw-cal">${cells}</div>
          <div class="bw-slots">
            ${state.selected ? `
              <h4>${esc(fmtDay(state.selected.dateObj))}</h4>
              ${slotsForDay && slotsForDay.length ? `
                <div class="bw-slot-list">
                  ${slotsForDay.map((s, i) => `
                    <button class="bw-slot" data-slot="${i}">${esc(fmtTime(s.start))}</button>
                  `).join('')}
                </div>
              ` : '<p class="bw-empty-msg">No slots on this day.</p>'}
            ` : '<p class="bw-empty-msg">Pick a date with available slots.</p>'}
          </div>
        </div>
      `;

      content.querySelectorAll('[data-month]').forEach(btn => {
        btn.addEventListener('click', () => {
          state.monthDate = new Date(state.monthDate.getFullYear(), state.monthDate.getMonth() + (+btn.dataset.month), 1);
          state.selected = null;
          load();
        });
      });
      content.querySelectorAll('[data-dur]').forEach(btn => {
        btn.addEventListener('click', () => {
          state.duration = parseInt(btn.dataset.dur, 10);
          state.selected = null;
          load();
        });
      });
      content.querySelectorAll('[data-day]').forEach(btn => {
        btn.addEventListener('click', () => {
          const key = btn.dataset.day;
          const [y, mo, d] = key.split('-').map(Number);
          state.selected = { dayKey: key, dateObj: new Date(y, mo - 1, d) };
          renderPicker();
        });
      });
      content.querySelectorAll('[data-slot]').forEach(btn => {
        btn.addEventListener('click', () => {
          const idx = +btn.dataset.slot;
          const slots = state.slotsByDay.get(state.selected.dayKey) || [];
          const s = slots[idx];
          state.selected.start = s.start;
          state.selected.end = s.end;
          renderForm();
        });
      });
    }

    function renderForm() {
      const fields = (state.data.registrationForm?.fields || []).filter(f =>
        f.questionId !== 'user_name' && f.questionId !== 'user_email'
      );
      content.innerHTML = `
        ${head()}
        <div class="bw-summary">
          <div>
            <span class="bw-tag">Selected</span>
            <strong>${esc(fmtDay(state.selected.start))} · ${esc(fmtTime(state.selected.start))}</strong>
          </div>
          <button class="bw-link" id="bw-change">Change</button>
        </div>
        <form class="bw-form" id="bw-form" novalidate>
          <label>Your name<input name="name" required value="${esc(state.form.name)}" placeholder="Jane Doe"/></label>
          <label>Email<input name="email" type="email" required value="${esc(state.form.email)}" placeholder="jane@example.com"/></label>
          ${fields.map(f => {
            const id = esc(f.questionId);
            const q = esc(f.questionText);
            const req = f.required ? 'required' : '';
            if (f.questionId === 'user_phone_number') {
              return `<label>${q}<input name="${id}" type="tel" ${req} placeholder="+1 555 555 0100"/></label>`;
            }
            return `<label>${q}<input name="${id}" ${req}/></label>`;
          }).join('')}
          <div class="bw-error" id="bw-form-error" hidden></div>
          <div class="wise-modal-actions">
            <button type="button" class="btn btn-ghost" id="bw-back">Back</button>
            <button type="submit" class="btn btn-primary">Confirm booking</button>
          </div>
        </form>
      `;
      document.getElementById('bw-change').addEventListener('click', () => renderPicker());
      document.getElementById('bw-back').addEventListener('click', () => renderPicker());
      document.getElementById('bw-form').addEventListener('submit', submit);
    }

    async function submit(e) {
      e.preventDefault();
      const fd = new FormData(e.target);
      const name = fd.get('name').trim();
      const email = fd.get('email').trim().toLowerCase();
      state.form.name = name; state.form.email = email;
      // Build answers in the same shape the Wise SPA sends — including
      // user_name and user_email (the registration form expects them even
      // though they're also passed as userName/userEmail at the top level).
      const answers = [
        { questionId: 'user_name', answer: name },
        { questionId: 'user_email', answer: email },
      ];
      for (const [k, v] of fd.entries()) {
        if (k === 'name' || k === 'email') continue;
        if (v) answers.push({ questionId: k, answer: String(v).trim() });
      }

      const errEl = document.getElementById('bw-form-error');
      errEl.hidden = true;
      const btn = e.target.querySelector('button[type=submit]');
      btn.disabled = true; btn.textContent = 'Booking…';

      try {
        const res = await bookSession(state.data.demoRoom._id, {
          userName: name,
          userEmail: email,
          scheduledStartTime: state.selected.start.toISOString(),
          scheduledEndTime: state.selected.end.toISOString(),
          timezone: TZ,
          answers,
        });
        renderSuccess();
      } catch (ex) {
        btn.disabled = false; btn.textContent = 'Confirm booking';
        errEl.hidden = false;
        errEl.textContent = ex.message || 'Could not complete booking.';
      }
    }

    function renderSuccess() {
      content.innerHTML = `
        ${head()}
        <div class="bw-success">
          <div class="bw-check">✓</div>
          <h3>You're booked!</h3>
          <p>${esc(fmtDay(state.selected.start))}<br>${esc(fmtTime(state.selected.start))} – ${esc(fmtTime(state.selected.end))} (${esc(TZ)})</p>
          <p class="bw-muted">A confirmation email is on the way to <strong>${esc(state.form.email)}</strong>.</p>
          <div class="wise-modal-actions">
            <button class="btn btn-primary" data-close>Done</button>
          </div>
        </div>
      `;
    }

    modal.classList.add('open');
    load();
  };
})();

// Tutor profile page: loads one tutor by ?id= (class_id) and renders the full
// profile with consultation iframe + Wise initiateFeePayment integration.
(async function () {
  const root = document.querySelector('[data-tutor-detail] .container');
  if (!root) return;

  const params = new URLSearchParams(location.search);
  const classId = params.get('id');
  const paymentOrderId = params.get('payment_order_id') || params.get('paymentOrderId');

  function escape(s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  function priceLabel(p) {
    if (!p || !p.value) return 'Free';
    const sym = p.currency === 'USD' ? '$' : (p.currency || '') + ' ';
    return `${sym}${p.value}`;
  }

  let tutors;
  try {
    tutors = await fetch('assets/tutors-data.json', { cache: 'no-cache' }).then(r => r.json());
  } catch (e) {
    root.innerHTML = '<p class="loading">Could not load tutor data.</p>';
    return;
  }
  const t = tutors.find(x => x.class_id === classId);
  if (!t) {
    root.innerHTML = '<p class="loading">Tutor not found. <a href="tutors.html">← All tutors</a></p>';
    return;
  }
  document.title = `${t.name} — FrogFluent`;

  root.innerHTML = `
    <a class="back-link" href="tutors.html">← All tutors</a>
    <div class="tutor-detail-grid">
      <aside class="tutor-detail-card">
        <img class="tutor-detail-photo" src="${escape(t.photo)}" alt="${escape(t.name)}"/>
        <h1>${escape(t.name)}</h1>
        <p class="meta">
          <span>📍 ${escape(t.country)}</span>
          <span>📚 Teaches ${escape(t.language)}</span>
          <span>⭐ 4.9/5 (new)</span>
        </p>
        <div class="price-row">
          <div>
            <span class="price-amount">${priceLabel(t.price)}</span>
            <span class="price-suffix"> / session</span>
          </div>
          <span class="trial-pill">Free trial available</span>
        </div>
        <div class="detail-actions">
          <button class="btn btn-outline btn-lg" id="trial-btn">Book a Free Trial</button>
          <button class="btn btn-primary btn-lg" id="pay-btn">Pay & Book Session</button>
        </div>
        <ul class="check-list small">
          ${(t.highlights || []).map(h => `<li>${escape(h)}</li>`).join('')}
        </ul>
      </aside>

      <main class="tutor-detail-body">
        <section>
          <h2>About ${escape(t.name.split(' ')[0])}</h2>
          <div class="tutor-bio">${formatBio(t.bio)}</div>
        </section>
        <section>
          <h2>What you'll get</h2>
          <ul class="check-list">
            ${(t.highlights || []).map(h => `<li>${escape(h)}</li>`).join('')}
          </ul>
        </section>
      </main>
    </div>
  `;

  function formatBio(bio) {
    if (!bio) return '<p>No bio available.</p>';
    const cleaned = String(bio).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    return cleaned
      .split(/(?<=[.!?])\s+(?=[A-Z])/)
      .reduce((acc, sentence) => {
        if (!acc.length || acc[acc.length - 1].length > 300) acc.push('');
        acc[acc.length - 1] = (acc[acc.length - 1] + ' ' + sentence).trim();
        return acc;
      }, [])
      .map(p => `<p>${escape(p)}</p>`)
      .join('');
  }

  // ---- Modal helpers ----
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
  const modalBody = modal.querySelector('.wise-modal-body');
  modal.addEventListener('click', e => {
    if (e.target.matches('[data-close]')) {
      modal.classList.remove('open');
      modalBody.classList.remove('wide');
    }
  });

  // ---- Book a Trial: opens Wise scheduler in a centered popup window
  //  Third-party cookies are blocked by default in iframes on modern browsers,
  //  which makes the Wise SPA's session fail and show "Demo not found!" after
  //  the page tries to read its session. A popup keeps the booking flow in
  //  first-party context and behaves exactly like Calendly/Cal.com integrations.
  document.getElementById('trial-btn').addEventListener('click', () => {
    if (typeof window.openBookingWidget === 'function') {
      window.openBookingWidget(t);
    } else {
      alert('Booking widget not loaded.');
    }
  });

  // ---- Pay: initiateFeePayment ----
  document.getElementById('pay-btn').addEventListener('click', () => {
    content.innerHTML = `
      <div class="wise-modal-head">
        <img src="${escape(t.photo)}" alt=""/>
        <div>
          <h3>Buy a session</h3>
          <p>${escape(t.name)} · ${priceLabel(t.price)} / 60 min</p>
        </div>
      </div>
      <form class="pay-form" id="pay-form">
        <label>Your name<input name="name" required placeholder="Jane Doe"/></label>
        <label>Email<input name="email" type="email" required placeholder="jane@example.com"/></label>
        <p class="pay-hint">You'll be redirected to a secure payment page to complete checkout.</p>
        <div class="wise-modal-actions">
          <button type="button" class="btn btn-ghost" data-close>Cancel</button>
          <button type="submit" class="btn btn-primary">Continue to Payment →</button>
        </div>
      </form>
      <div id="pay-error" class="pay-error" hidden></div>
    `;
    modal.classList.add('open');

    document.getElementById('pay-form').addEventListener('submit', async e => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const name = fd.get('name').trim();
      const email = fd.get('email').trim();
      const btn = e.target.querySelector('button[type=submit]');
      btn.disabled = true;
      btn.textContent = 'Initiating…';
      const err = document.getElementById('pay-error');
      err.hidden = true;

      const returnURL = `${location.origin}${location.pathname}?id=${encodeURIComponent(t.class_id)}`;
      try {
        const res = await fetch(`https://api.wiseapp.live/public/classes/${t.class_id}/initiateFeePayment`, {
          method: 'POST',
          headers: {
            'content-type': 'application/json',
            'x-wise-namespace': 'frogfluent-sample',
          },
          body: JSON.stringify({
            name,
            email,
            namespace: 'frogfluent-sample',
            classroomData: {
              paymentOptionId: t.payment_option_id,
              teacherId: t.teacher_id,
            },
            returnURL,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata',
          }),
        });
        const json = await res.json();
        if (json.status !== 200) throw new Error(json.message || 'Payment init failed');
        const payment = json.data?.paymentData;
        if (!payment?.payment_url) throw new Error('No payment URL returned');
        // Stash the payment_order_id so when the gateway redirects back we can verify
        sessionStorage.setItem('wise_pending_payment', payment.payment_order_id);
        location.href = payment.payment_url;
      } catch (ex) {
        btn.disabled = false;
        btn.textContent = 'Continue to Payment →';
        err.hidden = false;
        err.textContent = `Could not start payment: ${ex.message}`;
      }
    });
  });

  // ---- Payment status (set by payment_status.html after callback verification) ----
  const paymentStatus = (params.get('payment_status') || '').toLowerCase();
  const paymentState = params.get('payment_state') || '';
  if (paymentStatus === 'success' || paymentStatus === 'failed') {
    showPaymentResult(paymentStatus === 'success', paymentState);
  } else if (paymentOrderId) {
    // Fallback: verify directly if landed here without going through /payment_status/
    verifyAndShow(paymentOrderId);
  }

  function showPaymentResult(ok, state) {
    modalBody.classList.remove('wide');
    content.innerHTML = `
      <div class="wise-modal-head">
        <div style="font-size:42px;line-height:1">${ok ? '✅' : '⚠️'}</div>
        <div>
          <h3>${ok ? 'Payment successful' : 'Payment not confirmed'}</h3>
          <p>${ok ? 'Your session with ' + escape(t.name) + ' is being scheduled.' : 'Status: ' + escape(state || 'unknown')}</p>
        </div>
      </div>
      <div class="wise-modal-actions">
        <button class="btn btn-ghost" data-close>Close</button>
        ${ok ? `<a class="btn btn-primary" href="${escape(t.course_link)}" target="_blank" rel="noopener">Open my course →</a>` : ''}
      </div>
    `;
    modal.classList.add('open');
    sessionStorage.removeItem('wise_pending_payment');
    history.replaceState({}, '', location.pathname + '?id=' + encodeURIComponent(t.class_id));
  }

  async function verifyAndShow(orderId) {
    modalBody.classList.remove('wide');
    content.innerHTML = `
      <div class="wise-modal-head"><div><h3>Verifying payment…</h3><p>Please wait a moment.</p></div></div>
      <p class="pay-status">Checking with Wise…</p>
    `;
    modal.classList.add('open');
    try {
      const res = await fetch(`https://web.wise.live/api/v1/payments/payment_order/${orderId}/callback`);
      const json = await res.json();
      const status = (json.data?.status || json.status || '').toString().toUpperCase();
      const ok = ['SUCCESS', 'PAID', 'COMPLETED', 'CAPTURED', 'SUCCEEDED'].some(k => status.includes(k));
      showPaymentResult(ok, status);
    } catch (e) {
      content.innerHTML = `<p>Could not verify payment status. Please contact support.</p><div class="wise-modal-actions"><button class="btn btn-ghost" data-close>Close</button></div>`;
    }
  }
})();

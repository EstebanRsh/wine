const params = new URLSearchParams(location.search);
// En Vercel, usaremos rewrites para que /api/… apunte al backend en Render.
const API_BASE = '/api';

function currency(n) {
  try { return n.toLocaleString('es-AR', { style: 'currency', currency: 'ARS' }); } catch { return `$${n}` }
}

async function searchProducts() {
  const q = document.getElementById('q').value.trim();
  const url = q ? `${API_BASE}/products?q=${encodeURIComponent(q)}` : `${API_BASE}/products`;
  const res = await fetch(url);
  const items = await res.json();
  const $results = document.getElementById('results');
  $results.innerHTML = '';
  items.forEach(p => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <h3>${p.name} ${p.year ? '('+p.year+')' : ''}</h3>
      <div>${p.winery || ''} ${p.varietal ? '· ' + p.varietal : ''}</div>
      <div class="price">${currency(p.price_final)}
        ${p.promo_applied ? `<span class="badge">promo</span>` : ''}
      </div>
      <div class="note">Lista: ${currency(p.price_list)}</div>
      <a href="./product.html?pid=${encodeURIComponent(p.pid)}">Ver ficha</a>
    `;
    $results.appendChild(card);
  });
}

async function loadProduct() {
  const pid = params.get('pid');
  if (!pid) return;
  const res = await fetch(`${API_BASE}/products/${encodeURIComponent(pid)}`);
  if (res.status !== 200) {
    document.getElementById('product').innerHTML = '<p>No encontrado</p>';
    return;
  }
  const p = await res.json();
  const $el = document.getElementById('product');
  const promo = p.promo_applied;
  let promoText = '';
  if (promo) {
    if (promo.type === 'percent') promoText = `(-${promo.value}% aplicado)`;
    if (promo.type === 'two_for') promoText = `(2x por ${currency(promo.two_total)} → ${currency(promo.unit)} c/u)`;
  }
  $el.innerHTML = `
    <h2>${p.name} ${p.year ? '('+p.year+')' : ''}</h2>
    <div>${p.winery || ''} ${p.varietal ? '· ' + p.varietal : ''}</div>
    <p>${p.description || ''}</p>
    <div class="price">${currency(p.price_final)} <span class="note">Lista: ${currency(p.price_list)}</span></div>
    ${promo ? `<div class="badge">${promoText}</div>` : ''}
    <div>Estado: ${p.stock_status}</div>
  `;

  // QR con la URL actual (para imprimir en góndola)
  const qrDiv = document.getElementById('qrcode');
  qrDiv.innerHTML = '';
  const url = location.origin + location.pathname + '?pid=' + encodeURIComponent(p.pid);
  new QRCode(qrDiv, { text: url, width: 180, height: 180 });
}

window.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('btnSearch');
  if (btn) btn.addEventListener('click', searchProducts);
  const q = document.getElementById('q');
  if (q) q.addEventListener('keydown', (e) => { if (e.key === 'Enter') searchProducts(); });

  if (document.getElementById('results')) searchProducts();
  if (document.getElementById('product')) loadProduct();
});

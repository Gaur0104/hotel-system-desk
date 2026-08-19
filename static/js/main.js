// ── Sidebar toggle ──
document.getElementById('sidebarToggle')?.addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('collapsed');
  document.getElementById('page-content').classList.toggle('expanded');
});

// ── Dark Mode toggle ──
(function() {
  const toggle = document.getElementById('themeToggle');
  if (!toggle) return;
  const icon = toggle.querySelector('i');

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
    }
  }

  // Set icon on load
  const saved = localStorage.getItem('theme') || 'light';
  applyTheme(saved);

  toggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });
})();

// ── Auto-dismiss alerts after 4s ──
document.querySelectorAll('.alert').forEach(a => {
  setTimeout(() => { const bsAlert = bootstrap.Alert.getOrCreateInstance(a); bsAlert.close(); }, 4000);
});

// ── DataTables default init ──
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.datatable').forEach(tbl => {
    $(tbl).DataTable({
      pageLength: 15,
      order: [],
      language: { search: '<i class="bi bi-search"></i>', searchPlaceholder: ' Search...' },
      dom: "<'row'<'col-sm-6'l><'col-sm-6'f>>rt<'row'<'col-sm-6'i><'col-sm-6'p>>",
    });
  });
});

// ── Room availability check ──
function checkAvailability() {
  const ci = document.getElementById('check_in_date')?.value;
  const co = document.getElementById('check_out_date')?.value;
  const type = document.getElementById('room_type_filter')?.value || 'All';
  if (!ci || !co || ci >= co) {
    const sel = document.getElementById('room_id');
    if (sel) sel.innerHTML = '<option value="">Please select valid check-in and check-out dates.</option>';
    const preview = document.getElementById('price_preview');
    if (preview) preview.style.display = 'none';
    return;
  }
  fetch(`/api/available-rooms?check_in=${ci}&check_out=${co}&type=${type}`)
    .then(r => r.json())
    .then(rooms => {
      const sel = document.getElementById('room_id');
      if (!sel) return;
      sel.innerHTML = '';
      if (rooms.length === 0) {
        sel.innerHTML = '<option>No rooms available</option>';
        document.getElementById('price_preview').textContent = '';
        return;
      }
      rooms.forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.id;
        opt.dataset.price = r.price_per_night;
        opt.textContent = `Room ${r.room_number} — ${r.room_type} — ₹${r.price_per_night.toLocaleString('en-IN')}/night`;
        sel.appendChild(opt);
      });
      updatePricePreview();
    });
}

function updatePricePreview() {
  const sel = document.getElementById('room_id');
  const ci  = document.getElementById('check_in_date')?.value;
  const co  = document.getElementById('check_out_date')?.value;
  const preview = document.getElementById('price_preview');
  if (!sel || !ci || !co || !preview) return;
  const price = parseFloat(sel.options[sel.selectedIndex]?.dataset?.price || 0);
  const nights = Math.max(1, (new Date(co) - new Date(ci)) / 86400000);
  const charges = price * nights;
  const tax = charges * 0.12;
  preview.innerHTML = `<strong>₹${charges.toLocaleString('en-IN', {minimumFractionDigits:2})} + ₹${tax.toLocaleString('en-IN', {minimumFractionDigits:2})} GST = ₹${(charges+tax).toLocaleString('en-IN', {minimumFractionDigits:2})}</strong> &nbsp;|&nbsp; ${nights} night${nights>1?'s':''}`;
}

// ── Service total preview ──
function updateServiceTotal() {
  const qty   = parseFloat(document.getElementById('svc_qty')?.value || 1);
  const price = parseFloat(document.getElementById('svc_price')?.value || 0);
  const el = document.getElementById('svc_total');
  if (el) el.textContent = `Total: ₹${(qty * price).toLocaleString('en-IN', {minimumFractionDigits:2})}`;
}

// ── Quick service fill ──
function quickService(name, price) {
  const desc  = document.getElementById('svc_desc');
  const priceEl = document.getElementById('svc_price');
  if (desc)    desc.value = name;
  if (priceEl) priceEl.value = price;
  updateServiceTotal();
}

// ── Confirm delete ──
document.querySelectorAll('form.confirm-form').forEach(f => {
  f.addEventListener('submit', e => {
    if (!confirm(f.dataset.msg || 'Are you sure?')) e.preventDefault();
  });
});

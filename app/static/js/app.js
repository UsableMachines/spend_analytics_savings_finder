/* Theme toggle */
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme') || 'light';
  const next = current === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', next);
  const csrf = document.querySelector('meta[name="csrf-token"]');
  fetch('/api/theme', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrf ? csrf.content : '',
    },
    body: JSON.stringify({ theme: next }),
  }).catch(() => {});
}

/* Help panel */
function toggleHelp() {
  document.getElementById('helpPanel').classList.toggle('open');
  document.getElementById('helpOverlay').classList.toggle('open');
}

/* Auto-dismiss flash messages */
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.flash').forEach(function(el) {
    setTimeout(function() { el.style.opacity = '0'; setTimeout(function() { el.remove(); }, 300); }, 5000);
  });
});

/* Format currency */
function fmtCurrency(val) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

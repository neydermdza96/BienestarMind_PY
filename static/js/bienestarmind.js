/**
 * BienestarMind — JS Global
 * Utilidades UX: loading states, confirmaciones, shortcuts
 */

document.addEventListener('DOMContentLoaded', function () {

  // ── Loading en botones de submit ────────────────────────
  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function () {
      const btn = form.querySelector('button[type="submit"]');
      if (btn && !btn.classList.contains('no-loading')) {
        setTimeout(function () { btn.classList.add('btn-loading'); }, 50);
      }
    });
  });

  // ── Confirmar eliminaciones ──────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      const msg = el.getAttribute('data-confirm') || '¿Estás seguro?';
      if (!window.confirm(msg)) e.preventDefault();
    });
  });

  // ── Auto focus en primer input de modales Bootstrap ──────
  document.querySelectorAll('.modal').forEach(function (modal) {
    modal.addEventListener('shown.bs.modal', function () {
      const input = modal.querySelector('input:not([type="hidden"]), select, textarea');
      if (input) input.focus();
    });
  });

  // ── Marcar enlace activo del sidebar con URL actual ──────
  const currentPath = window.location.pathname;
  document.querySelectorAll('#sidebar a').forEach(function (link) {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // ── Tooltips Bootstrap ───────────────────────────────────
  if (typeof bootstrap !== 'undefined') {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
      new bootstrap.Tooltip(el);
    });
  }

  // ── Tabla: resaltar fila al click ─────────────────────────
  document.querySelectorAll('.bm-table tbody tr').forEach(function (row) {
    row.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' || e.target.closest('a') || e.target.closest('button')) return;
      document.querySelectorAll('.bm-table tbody tr.selected').forEach(r => r.classList.remove('selected'));
      row.classList.toggle('selected');
    });
  });

  // ── Atajos de teclado ────────────────────────────────────
  document.addEventListener('keydown', function (e) {
    // Alt+N → ir al botón "Nuevo"
    if (e.altKey && e.key === 'n') {
      const btnNuevo = document.querySelector('.btn-sena[href*="crear"], .btn-sena[href*="nuevo"]');
      if (btnNuevo) { e.preventDefault(); btnNuevo.click(); }
    }
    // Alt+B → volver
    if (e.altKey && e.key === 'b') {
      const btnVolver = document.querySelector('.btn-outline-sena[href="javascript:history.back()"], a[href*="javascript:history.back"]');
      if (btnVolver) { e.preventDefault(); history.back(); }
    }
    // Alt+R → focus en búsqueda
    if (e.altKey && e.key === 'r') {
      const searchInput = document.querySelector('.search-input');
      if (searchInput) { e.preventDefault(); searchInput.focus(); searchInput.select(); }
    }
    // Escape → limpiar búsqueda
    if (e.key === 'Escape') {
      const searchInput = document.querySelector('.search-input:focus');
      if (searchInput) searchInput.value = '';
    }
  });

  // ── Formatear cédulas al escribir ───────────────────────
  document.querySelectorAll('input[name="documento"]').forEach(function (input) {
    input.addEventListener('input', function () {
      this.value = this.value.replace(/[^0-9]/g, '');
    });
  });

  // ── Formatear teléfono ───────────────────────────────────
  document.querySelectorAll('input[name="telefono"]').forEach(function (input) {
    input.addEventListener('input', function () {
      this.value = this.value.replace(/[^0-9+]/g, '');
    });
  });

  // ── Mayúsculas automáticas en nombres ────────────────────
  document.querySelectorAll('input[name="nombres"], input[name="apellidos"]').forEach(function (input) {
    input.addEventListener('blur', function () {
      this.value = this.value.toUpperCase();
    });
  });

  // ── Contador de caracteres en textareas ──────────────────
  document.querySelectorAll('textarea[maxlength]').forEach(function (ta) {
    const max = ta.getAttribute('maxlength');
    const counter = document.createElement('small');
    counter.style.cssText = 'color:var(--texto-muted);float:right;font-size:11px;';
    ta.parentNode.appendChild(counter);
    const update = () => counter.textContent = `${ta.value.length}/${max}`;
    ta.addEventListener('input', update);
    update();
  });

  console.log('🧠 BienestarMind SENA — Sistema iniciado');
});

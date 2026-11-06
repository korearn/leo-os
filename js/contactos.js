// Contactos: cuenta los "conectados" de cada grupo, como en MSN, y filtra con el buscador.
(function () {
  var grupos = Array.prototype.slice.call(document.querySelectorAll('.msn__grupo'));
  function contar() {
    grupos.forEach(function (g) {
      var todos = g.querySelectorAll('.contacto');
      var vis = Array.prototype.filter.call(todos, function (c) { return !c.hidden; });
      var on = vis.filter(function (c) { return !c.classList.contains('contacto--off'); }).length;
      var n = g.querySelector('.msn__cuenta');
      if (n) n.textContent = '(' + (g.querySelector('.contacto--off') ? vis.length : on + '/' + vis.length) + ')';
      g.hidden = vis.length === 0;
    });
  }
  var filtro = document.getElementById('msn-filtro');
  if (filtro) {
    filtro.addEventListener('input', function () {
      var q = filtro.value.trim().toLowerCase();
      document.querySelectorAll('.contacto').forEach(function (c) {
        c.hidden = q && c.textContent.toLowerCase().indexOf(q) === -1;
      });
      if (q) grupos.forEach(function (g) { g.open = true; });
      contar();
    });
  }
  contar();
})();

// Música: los estuches de CD se pueden "abrir". Al pasar el mouse el disco asoma y gira;
// al hacer clic se queda girando y aparece su nota como un inserto de papel.
// Sin JavaScript, las notas se ven siempre (como antes).
(function () {
  var lista = document.querySelector('.cds');
  if (!lista) return;
  var discos = Array.prototype.slice.call(lista.querySelectorAll('.cd'));
  if (!discos.length) return;
  lista.classList.add('cds--interactivo');

  function cerrarTodos(excepto) {
    discos.forEach(function (d) {
      if (d !== excepto) { d.classList.remove('cd--abierto'); d.setAttribute('aria-expanded', 'false'); }
    });
  }
  discos.forEach(function (d) {
    var titulo = d.querySelector('.cd__title');
    d.setAttribute('role', 'button');
    d.setAttribute('tabindex', '0');
    d.setAttribute('aria-expanded', 'false');
    if (titulo) d.setAttribute('aria-label', 'Abrir ' + titulo.textContent.trim());
    function alternar() {
      var abrir = !d.classList.contains('cd--abierto');
      cerrarTodos(d);
      d.classList.toggle('cd--abierto', abrir);
      d.setAttribute('aria-expanded', String(abrir));
    }
    d.addEventListener('click', alternar);
    d.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); alternar(); }
      if (ev.key === 'Escape') cerrarTodos(null);
    });
  });
})();

// Cartel de bandas y géneros: clic en una banda abre su CD; clic en un género ilumina
// los discos y bandas que lo tienen (otro clic lo apaga). Sin JS, las bandas son enlaces al CD.
(function () {
  var discos = Array.prototype.slice.call(document.querySelectorAll('.cd[data-generos]'));
  var bandas = Array.prototype.slice.call(document.querySelectorAll('.cartel .banda'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip[data-genero]'));

  bandas.forEach(function (b) {
    var a = b.querySelector('a[href^="#cd-"]');
    if (!a) return;
    a.addEventListener('click', function (ev) {
      var cd = document.getElementById(a.getAttribute('href').slice(1));
      if (!cd) return;
      ev.preventDefault();
      cd.scrollIntoView({ behavior: 'smooth', block: 'center' });
      if (!cd.classList.contains('cd--abierto')) cd.click();
      cd.classList.remove('cd--llamada'); void cd.offsetWidth; cd.classList.add('cd--llamada');
    });
  });

  function tiene(el, g) { return (el.getAttribute('data-generos') || '').split('|').indexOf(g) !== -1; }
  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      var g = c.getAttribute('data-genero');
      var activo = c.getAttribute('aria-pressed') !== 'true';
      chips.forEach(function (o) { o.setAttribute('aria-pressed', String(o === c && activo)); });
      document.body.classList.toggle('filtro-genero', activo);
      discos.concat(bandas).forEach(function (el) {
        el.classList.toggle('es-genero', activo && tiene(el, g));
      });
    });
  });
})();

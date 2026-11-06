// Cine: los boletos se "rompen" con un clic. El talón se desprende y del otro lado
// aparece el reverso: quién la dirige, el género y de qué trata (sale de Movies.md vía cine_sync.py).
// Sin JavaScript, el reverso se ve siempre debajo de la nota.
(function () {
  var lista = document.querySelector('.tickets');
  if (!lista) return;
  var boletos = Array.prototype.slice.call(lista.querySelectorAll('.ticket'))
    .filter(function (b) { return b.querySelector('.ticket__back'); });
  if (!boletos.length) return;
  lista.classList.add('tickets--interactivo');
  boletos.forEach(function (b) {
    var t = b.querySelector('.ticket__title');
    b.setAttribute('role', 'button');
    b.setAttribute('tabindex', '0');
    b.setAttribute('aria-pressed', 'false');
    if (t) b.setAttribute('aria-label', 'Romper el boleto de ' + t.textContent.trim());
    function alternar() {
      var roto = b.classList.toggle('ticket--roto');
      b.setAttribute('aria-pressed', String(roto));
    }
    b.addEventListener('click', alternar);
    b.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); alternar(); }
    });
  });
})();

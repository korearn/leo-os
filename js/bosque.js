// Bosque perdido: hay que seguir a la luciérnaga. Cuatro claros seguidos y llegas al centro.
// Si te equivocas de camino, el bosque te regresa al inicio (como debe ser).
(function () {
  var CAMINO = ['n', 'o', 'n', 'e'];        // la luciérnaga siempre se posa junto al camino correcto
  var paso = 0;
  var rosa = document.getElementById('b-rosa');
  var luz = document.getElementById('b-luz');
  var claro = document.getElementById('b-claro');
  var titulo = document.getElementById('b-titulo');
  var texto = document.getElementById('b-texto');
  if (!rosa) return;

  var POS = { n: ['50%', '-6px'], s: ['50%', '100%'], e: ['100%', '50%'], o: ['-6px', '50%'] };
  function ponerLuz() {
    var p = POS[CAMINO[paso]];
    luz.style.left = p[0]; luz.style.top = p[1];
  }
  function niebla(fn) {
    document.body.classList.add('bosque--niebla');
    setTimeout(function () { fn(); document.body.classList.remove('bosque--niebla'); }, 420);
  }
  rosa.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-dir]');
    if (!b) return;
    var dir = b.dataset.dir;
    niebla(function () {
      if (dir === CAMINO[paso]) {
        paso++;
        if (paso === CAMINO.length) return llegar();
        claro.textContent = 'claro_0' + (paso + 1);
        titulo.textContent = 'Más adentro';
        texto.textContent = ['Los mismos árboles. La luz sigue ahí.', 'Se oye algo, como una flauta lejos.',
          'La niebla se abre un poco.'][paso - 1] || '';
      } else {
        paso = 0;
        claro.textContent = 'claro_01';
        titulo.textContent = 'Te perdiste';
        texto.textContent = 'Este lugar ya lo habías visto… volviste al principio.';
      }
      ponerLuz();
    });
  });
  function llegar() {
    document.body.classList.add('bosque--centro');
    claro.textContent = 'centro';
    titulo.textContent = 'El centro del bosque';
    texto.innerHTML = 'Aquí no hay nada… salvo un blinkie tirado en el pasto. Supongo que es tuyo ahora.';
    rosa.innerHTML = '<img class="bosque__premio" src="img/blinkies/explora.gif" alt="¿Y si exploras?" width="150" height="20">';
    if (window.leosLogro) window.leosLogro('bosque_centro');
  }
  ponerLuz();
})();

// Videojuegos: efecto de "meter" el cartucho y el botón "Saca uno al azar".
// Va en archivo aparte: la política de seguridad (CSP) de Neocities puede bloquear el JavaScript escrito dentro del HTML.
// Sin JavaScript la página funciona igual (la consola usa radios + CSS); esto solo agrega detalles.

(function () {
  // El cartucho elegido sube a la ranura
  var carts = document.querySelectorAll('.insert__carts .game');
  function marcar() {
    carts.forEach(function (li) {
      var lab = li.querySelector('label');
      var input = lab && document.getElementById(lab.htmlFor);
      li.classList.toggle('is-in', !!(input && input.checked));
    });
  }
  var screen = document.querySelector('.insert__screen');
  function verPantalla() {
    if (!screen) return;
    var r = screen.getBoundingClientRect();
    if (r.top < 0 || r.bottom > window.innerHeight) screen.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
  document.querySelectorAll('.insert input[name="cart"]').forEach(function (r) {
    r.addEventListener('change', function () { marcar(); verPantalla(); });
  });
  // "¿Te gustó? Prueba..." cambia de cartucho sin mover la vista
  document.querySelectorAll('.insert__jump').forEach(function (l) {
    l.addEventListener('click', function () { setTimeout(marcar, 0); });
  });
})();

(function () {
  // Saca un juego al azar de la caja (Clásicos y Modernos)
  var box = document.querySelector('.random');
  if (!box) return;
  var items = Array.prototype.slice.call(document.querySelectorAll('#todos .gamelist__items li'));
  if (!items.length) return;
  var out = box.querySelector('.random__out');
  var btn = box.querySelector('.random__btn');
  box.hidden = false;
  btn.addEventListener('click', function () {
    var li = items[Math.floor(Math.random() * items.length)];
    var t = function (sel) { var n = li.querySelector(sel); return n ? n.textContent.trim() : ''; };
    var plat = t('.gl__plat');
    var consola = plat;
    if (!consola) {
      // en Clásicos la consola es el título de su grupo
      var h = li.closest('ul').previousElementSibling;
      consola = h && h.classList.contains('gamelist__console') ? h.firstChild.textContent.trim() : '';
    }
    var meta = [consola, t('.gl__year')].filter(Boolean).join(' · ');
    out.innerHTML = '';
    out.appendChild(document.createTextNode('▶ ' + t('.gl__name') + ' '));
    var s = document.createElement('small');
    s.textContent = meta;
    out.appendChild(s);
  });
})();

(function () {
  // Tips de "pantalla de carga" mientras no hay cartucho puesto
  var idle = document.querySelector('.insert__idle');
  if (!idle) return;
  var TIPS = [
    'Hay 8 estrellas escondidas en LeOS. A ver cuántas encuentras.',
    'La ranura ??? del menú HOME no va a estar vacía para siempre.',
    'En la Galería puedes pasar las fotos con las flechas del teclado.',
    'La tele de Anime tiene botones de canal. Haz zapping.',
    'Los estuches de Música se abren con un clic.',
    'Si no sabes cuál elegir, abajo puedes sacar uno al azar.',
    'Firma el libro de visitas y déjame una recomendación.',
    'Guarda tu partida seguido.',
    'No apagues la consola mientras se guarda.'
  ];
  var p = document.createElement('p');
  p.className = 'insert__tip';
  idle.insertAdjacentElement('afterend', p);
  var i = Math.floor(Math.random() * TIPS.length);
  function siguiente() { p.textContent = 'TIP: ' + TIPS[i % TIPS.length]; i++; }
  siguiente();
  setInterval(siguiente, 6500);
})();

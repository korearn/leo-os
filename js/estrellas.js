// Estrellas escondidas: una en cada página. Al juntarlas todas se abre la ranura "???" del menú HOME.
// Para mover una estrella, cambia su selector y posición aquí (el escondite se inyecta al cargar la página).
// Se guardan en el navegador del visitante (localStorage), así que cada quien tiene su propio avance.
(function () {
  var ESCONDITES = {
    // página: [id, selector donde se esconde, posición dentro de ese elemento]
    'index':    ['home',     '.ds__lid',                     { right: '8px', bottom: '6px' }],
    'juegos':   ['juegos',   '.insert__tv',                  { left: '6px', bottom: '6px' }],
    'musica':   ['musica',   '.player__cover',               { right: '4px', top: '4px' }],
    'anime':    ['anime',    '.tv__grille',                  { right: '2px', bottom: '2px' }],
    'cine':     ['cine',     '.tickets .ticket:nth-child(5) .ticket__stub', { right: '3px', bottom: '3px' }],
    'galeria':  ['galeria',  '.gallery .shot:nth-child(9) .shot__frame', { right: '10px', top: '10px' }],
    'sobre-mi': ['sobre-mi', '.profile__avatar',             { right: '2px', bottom: '2px' }],
    'libro':    ['libro',    '.prompts',                     { right: '6px', top: '4px' }]
  };
  var TOTAL = Object.keys(ESCONDITES).length;
  var CLAVE = 'leos-estrellas';

  function leer() {
    try { return JSON.parse(localStorage.getItem(CLAVE)) || []; } catch (e) { return []; }
  }
  function guardar(lista) {
    try { localStorage.setItem(CLAVE, JSON.stringify(lista)); } catch (e) {}
  }

  // Globo de notificación estilo Windows XP
  function globo(titulo, texto) {
    var viejo = document.querySelector('.globo');
    if (viejo) viejo.remove();
    var g = document.createElement('div');
    g.className = 'globo';
    g.setAttribute('role', 'status');
    g.innerHTML = '<p class="globo__titulo"><img src="img/sprites/estrella.gif" alt="" width="11" height="11"> ' +
      titulo + '</p><p class="globo__texto">' + texto + '</p>';
    var cerrar = document.createElement('button');
    cerrar.className = 'globo__x'; cerrar.type = 'button'; cerrar.setAttribute('aria-label', 'Cerrar'); cerrar.textContent = '×';
    cerrar.addEventListener('click', function () { g.remove(); });
    g.appendChild(cerrar);
    document.body.appendChild(g);
    setTimeout(function () { g.classList.add('globo--fuera'); }, 5200);
    setTimeout(function () { g.remove(); }, 5800);
  }

  // Lo que cambia en la portada según el avance
  function pintarPortada(lista) {
    var cuenta = document.querySelector('.js-estrellas');
    if (cuenta) {
      cuenta.hidden = lista.length === 0;
      cuenta.textContent = '★ ' + lista.length + '/' + TOTAL;
    }
    var ranura = document.querySelector('.app--vacia');
    if (ranura && lista.length >= TOTAL && !ranura.dataset.abierta) {
      var a = document.createElement('a');
      a.className = 'app app--abierta';
      a.href = 'fuera.html';
      a.title = '???';
      a.innerHTML = '<span class="app__glitch" aria-hidden="true"></span><span class="app__name">???</span>';
      ranura.replaceWith(a);
    }
  }

  // Palancas del debug_room (zona oculta): noclip y show_stars
  try {
    var flags = JSON.parse(localStorage.getItem('leos-flags')) || {};
    if (flags.noclip) document.body.classList.add('noclip');
    if (flags.verEstrellas) document.body.classList.add('ver-estrellas');
  } catch (e) {}

  var pagina = (location.pathname.split('/').pop() || 'index').replace('.html', '') || 'index';
  var lista = leer();
  pintarPortada(lista);

  var datos = ESCONDITES[pagina];
  if (!datos) return;
  var id = datos[0];
  if (lista.indexOf(id) !== -1) return; // ya la encontró
  var lugar = document.querySelector(datos[1]);
  if (!lugar) return;
  if (getComputedStyle(lugar).position === 'static') lugar.style.position = 'relative';

  var b = document.createElement('button');
  b.type = 'button';
  b.className = 'estrella';
  b.setAttribute('aria-label', 'Una estrella escondida');
  for (var k in datos[2]) b.style[k] = datos[2][k];
  b.innerHTML = '<img src="img/sprites/estrella.gif" alt="" width="11" height="11">';
  b.addEventListener('click', function (ev) {
    ev.preventDefault(); ev.stopPropagation();
    var l = leer();
    if (l.indexOf(id) === -1) l.push(id);
    guardar(l);
    b.classList.add('estrella--tomada');
    setTimeout(function () { b.remove(); }, 700);
    if (l.length >= TOTAL) {
      globo('¡Las ' + TOTAL + ' estrellas!', 'Algo se abrió en el menú HOME…');
    } else {
      globo('Encontraste una estrella', 'Llevas ' + l.length + ' de ' + TOTAL + '. Las demás están escondidas en otras páginas.');
    }
    pintarPortada(l);
  });
  lugar.appendChild(b);
})();

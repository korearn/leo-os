// La mascota de LeOS: un alien de pixel que se pasea por la orilla de abajo de la pantalla.
// Al pasar el mouse se detiene; al hacerle clic dice algo. Solo aparece en pantallas anchas (ver .mascota en style.css).
(function () {
  var FRASES = [
    '¡Hola, terrícola! 👽',
    '¿Ya encontraste las 8 estrellas?',
    'Firma el libro de visitas, porfa.',
    'Este sitio se ve mejor de noche.',
    'Yo también vengo de 2003.',
    '¿Has probado hacer zapping en Anime?',
    'Dicen que hay algo detrás de la ranura ???…',
    'No me sigas, que me pierdo.'
  ];
  var m = document.createElement('button');
  m.type = 'button';
  m.className = 'mascota';
  m.setAttribute('aria-label', 'La mascota de LeOS');
  m.innerHTML = '<span class="mascota__cuerpo" aria-hidden="true"></span>';
  var globo = document.createElement('span');
  globo.className = 'mascota__globo';
  globo.setAttribute('role', 'status');
  m.appendChild(globo);
  var ultimo = -1, t;
  m.addEventListener('click', function () {
    var i;
    do { i = Math.floor(Math.random() * FRASES.length); } while (i === ultimo && FRASES.length > 1);
    ultimo = i;
    globo.textContent = FRASES[i];
    m.classList.add('mascota--habla');
    clearTimeout(t);
    t = setTimeout(function () { m.classList.remove('mascota--habla'); }, 3200);
  });
  document.body.appendChild(m);
})();

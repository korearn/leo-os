// La tele de Anime: zapping entre los favoritos (las cintas VHS de "Mis favoritos").
// Botones de canal ▲ ▼ con estática entre canal y canal; también se puede "meter" una cinta haciéndole clic.
// Sin JavaScript, la tele muestra lo que haya generado anime_sync.py entre los marcadores anime:tv.
(function () {
  var tv = document.querySelector('.tv');
  var pantalla = tv && tv.querySelector('.tv__screen');
  var cintas = Array.prototype.slice.call(document.querySelectorAll('.vhs .tape'));
  if (!tv || !pantalla || !cintas.length) return;

  var canales = cintas.map(function (c) {
    var etiqueta = c.querySelector('.tape__label');
    var anio = c.querySelector('.tape__year');
    var nota = c.querySelector('.tape__note');
    var nombre = etiqueta ? etiqueta.childNodes[0].textContent.trim() : '';
    return {
      nombre: nombre,
      anio: anio ? anio.textContent.trim() : '',
      nota: nota ? nota.textContent.trim() : '',
      color: c.style.getPropertyValue('--tape') || '#5fe0ff'
    };
  });
  var actual = 0;

  tv.classList.add('tv--zapping');
  var osd = pantalla.querySelector('.tv__osd');
  var canal = document.createElement('div');
  canal.className = 'tv__canal';
  canal.setAttribute('aria-live', 'polite');
  canal.innerHTML = '<p class="tv__num"></p><p class="tv__titulo"></p><p class="tv__anio"></p><p class="tv__sinopsis"></p>';
  pantalla.appendChild(canal);
  var ruido = document.createElement('img');
  ruido.className = 'tv__ruido'; ruido.src = 'img/3ds/anime.gif'; ruido.alt = ''; ruido.hidden = true;
  pantalla.appendChild(ruido);

  // Botones de canal en el panel de la tele (las perillas y la rejilla siguen siendo adorno)
  var panel = tv.querySelector('.tv__panel');
  panel.removeAttribute('aria-hidden');
  Array.prototype.forEach.call(panel.children, function (el) { el.setAttribute('aria-hidden', 'true'); });
  var botones = document.createElement('div');
  botones.className = 'tv__botones';
  botones.innerHTML = '<button type="button" class="tv__btn" data-ir="-1" aria-label="Canal anterior">▲</button>' +
    '<span class="tv__btn-label" aria-hidden="true">CH</span>' +
    '<button type="button" class="tv__btn" data-ir="1" aria-label="Canal siguiente">▼</button>';
  panel.insertBefore(botones, panel.querySelector('.tv__led'));

  function dos(n) { return (n < 10 ? '0' : '') + n; }
  function sintonizar(i, conRuido) {
    actual = (i + canales.length) % canales.length;
    var c = canales[actual];
    function pintar() {
      if (osd) osd.textContent = 'Mis favoritos · ' + (actual + 1) + '/' + canales.length;
      canal.querySelector('.tv__num').textContent = 'CH ' + dos(actual + 1);
      canal.querySelector('.tv__titulo').textContent = c.nombre;
      canal.querySelector('.tv__anio').textContent = c.anio;
      canal.querySelector('.tv__sinopsis').textContent = c.nota;
      canal.style.setProperty('--canal', c.color);
      cintas.forEach(function (t, k) { t.classList.toggle('tape--puesta', k === actual); });
    }
    if (conRuido) {
      ruido.hidden = false;
      setTimeout(function () { pintar(); }, 160);
      setTimeout(function () { ruido.hidden = true; }, 380);
    } else {
      pintar();
    }
  }

  botones.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-ir]');
    if (b) sintonizar(actual + Number(b.dataset.ir), true);
  });
  cintas.forEach(function (t, k) {
    t.setAttribute('role', 'button');
    t.setAttribute('tabindex', '0');
    t.setAttribute('title', 'Meter esta cinta a la tele');
    t.addEventListener('click', function () { sintonizar(k, true); pantalla.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); });
    t.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); sintonizar(k, true); }
    });
  });

  sintonizar(0, false);
})();

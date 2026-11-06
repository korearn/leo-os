// Portada: reloj de la barra de estado, contador en vivo y botón 88x31.
// Va en archivo aparte: la política de seguridad (CSP) de Neocities puede bloquear el JavaScript escrito dentro del HTML.

// Relojes (barra de estado y pantalla de la 3DS) y fecha de la 3DS
(function () {
  var relojes = document.querySelectorAll('.js-reloj');
  var fechas = document.querySelectorAll('.js-fecha');
  function tick() {
    var d = new Date();
    var hora = d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
    var fecha = d.toLocaleDateString('es-MX', { day: '2-digit', month: '2-digit' });
    relojes.forEach(function (el) {
      el.textContent = hora;
      if (el.tagName === 'TIME') el.setAttribute('datetime', d.toISOString());
    });
    fechas.forEach(function (el) { el.textContent = fecha; });
  }
  tick();
  setInterval(tick, 30000);
})();

// Contador de visitas. El número sale de js/contador.js, que GitHub Actions sube a Neocities
// una o dos veces al día (.github/workflows/contador.yml) con las visitas de la API de Neocities.
// Si ese archivo no está (por ejemplo, abriendo el sitio en local), se queda el del último sync.
// (Pedirlo en vivo a la API no sirve: la CSP de Neocities gratis bloquea fetch a otros dominios.)
// También calcula la próxima キリ番 (kiriban): centenas, números repetidos (777, 1111) y el 666.
(function () {
  var el = document.getElementById('visitas');
  var kiri = document.querySelector('.js-kiriban');
  if (!el) return;

  function esKiriban(n) {
    var t = String(n);
    return n > 0 && (n % 100 === 0 || /^(\d)\1+$/.test(t) && t.length >= 3 || n === 666);
  }
  function pintarKiriban(n) {
    if (!kiri) return;
    var caja = kiri.parentNode;
    if (esKiriban(n)) {
      caja.classList.add('kiriban--hoy');
      caja.innerHTML = '<span class="jp" lang="ja">キリ番ゲット!</span> Eres el <b>' +
        String(n).padStart(6, '0') + '</b>. Toma captura y fírmalo en el libro.';
      return;
    }
    var m = n + 1;
    while (!esKiriban(m)) m++;
    kiri.textContent = String(m).padStart(6, '0');
  }

  var n = parseInt(el.textContent.replace(/\D/g, ''), 10) || 0;
  var vivo = parseInt(window.LEOS_VISITAS, 10);
  if (vivo > n) {
    n = vivo;
    el.innerHTML = String(n).padStart(6, '0').split('').map(function (c) { return '<span>' + c + '</span>'; }).join('');
  }
  pintarKiriban(n);
})();

// Al hacer clic en el código de un botón o banner, se selecciona todo para copiarlo.
(function () {
  document.querySelectorAll('textarea.code').forEach(function (t) {
    t.addEventListener('click', function () { t.select(); });
  });
})();

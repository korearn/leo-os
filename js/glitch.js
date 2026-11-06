// glitch_city: un mapa de tiles de 8x8 hecho con basura de memoria. Se redibujan pedazos al azar.
(function () {
  var c = document.getElementById('g-mapa');
  if (!c || !c.getContext) return;
  var g = c.getContext('2d');
  var PAL = ['#000000', '#120f2e', '#2a2463', '#7b5cff', '#5fe0ff', '#e8f4ff', '#e2231a', '#ffc20e', '#00a650', '#9aa6d6'];
  var TILES = [];
  // 24 tiles "corruptos": rayas, ruido, bloques y medios tiles
  for (var t = 0; t < 24; t++) {
    var px = [];
    var a = PAL[(t * 7) % PAL.length], b = PAL[(t * 3 + 1) % PAL.length];
    for (var y = 0; y < 8; y++) for (var x = 0; x < 8; x++) {
      var v;
      switch (t % 6) {
        case 0: v = (x + y) % 3 === 0; break;
        case 1: v = y < 4; break;
        case 2: v = Math.random() < .5; break;
        case 3: v = x % 2 === 0 && y % 3 !== 0; break;
        case 4: v = (x * y) % 5 < 2; break;
        default: v = x > y;
      }
      px.push(v ? a : b);
    }
    TILES.push(px);
  }
  var W = c.width / 8, H = c.height / 8;
  var mapa = [];
  for (var i = 0; i < W * H; i++) mapa.push(Math.floor(Math.random() * TILES.length));
  function tile(i) {
    var tx = (i % W) * 8, ty = Math.floor(i / W) * 8, px = TILES[mapa[i]];
    for (var k = 0; k < 64; k++) { g.fillStyle = px[k]; g.fillRect(tx + (k % 8), ty + Math.floor(k / 8), 1, 1); }
  }
  for (var j = 0; j < mapa.length; j++) tile(j);
  var quieto = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (quieto) return;
  setInterval(function () {
    var n = 6 + Math.floor(Math.random() * 30);
    var inicio = Math.floor(Math.random() * mapa.length);
    for (var k = 0; k < n; k++) {
      var i = (inicio + k) % mapa.length;
      mapa[i] = (mapa[i] + 1 + Math.floor(Math.random() * 5)) % TILES.length;
      tile(i);
    }
  }, 220);
})();

// Mojibake: el botón cambia la "codificación" y el texto se vuelve legible (japonés + traducción).
(function () {
  var btn = document.querySelector('.mojibake__btn');
  if (!btn) return;
  btn.hidden = false;
  var piezas = Array.prototype.slice.call(document.querySelectorAll('.mojibake [data-ok]'));
  var basura = piezas.map(function (el) { return el.textContent; });
  var leido = false;
  btn.addEventListener('click', function () {
    leido = !leido;
    btn.textContent = leido ? '文字コード: UTF-8 ▾' : '文字コード: Shift_JIS ▾';
    piezas.forEach(function (el, i) {
      if (leido) {
        el.textContent = el.getAttribute('data-ok');
        var es = document.createElement('small');
        es.className = 'mojibake__es';
        es.lang = 'es';
        es.textContent = el.getAttribute('data-es');
        el.appendChild(document.createElement('br'));
        el.appendChild(es);
      } else {
        el.textContent = basura[i];
      }
    });
    document.querySelector('.mojibake').classList.toggle('mojibake--ok', leido);
  });
})();

// Radio pirata (zona oculta): minijuego de sintonía.
// - La frecuencia correcta sale de la fecha (misma para todos ese día), entre 88.1 y 107.9 MHz.
// - Entre más cerca, menos estática y más barras. Hay que quedarse en la frecuencia un momento.
// - Al encontrarla se muestra el chat de Cbox (src en data-cbox de #r-chat) y se marca el logro "radio".
// - Si ya la encontraste hoy, al volver la radio sale sintonizada.
(function () {
  var perilla = document.getElementById('r-perilla');
  if (!perilla) return;
  var frec = document.getElementById('r-frec');
  var estado = document.getElementById('r-estado');
  var barras = document.querySelectorAll('.radio__barras i');
  var lienzo = document.getElementById('r-estatica');
  var chat = document.getElementById('r-chat');
  var marco = document.getElementById('r-marco');
  var btnSonido = document.getElementById('r-sonido');
  var radio = document.getElementById('radio');

  // Frecuencia del día
  var d = new Date();
  var hoy = d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate();
  var h = 7;
  for (var i = 0; i < hoy.length; i++) h = (h * 31 + hoy.charCodeAt(i)) % 100003;
  var CANALES = 100;                                  // 88.1, 88.3, … 107.9
  var objetivo = 88.1 + 0.2 * (h % CANALES);
  objetivo = Math.round(objetivo * 10) / 10;

  var encontrada = false, sostener = null, fuerza = 0;

  function leer(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function guardar(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // Estática en el "bocina"
  var g = lienzo.getContext && lienzo.getContext('2d');
  var img = g && g.createImageData(lienzo.width, lienzo.height);
  var quieto = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function ruido() {
    if (!g) return;
    var px = img.data, nivel = 1 - fuerza;
    for (var k = 0; k < px.length; k += 4) {
      var v = Math.random() < nivel ? Math.random() * 255 : 18;
      px[k] = v * .6; px[k + 1] = v * .65; px[k + 2] = v; px[k + 3] = 255;
    }
    g.putImageData(img, 0, 0);
  }

  // Sonido opcional (solo si el visitante lo prende)
  var audio = null;
  function prenderSonido() {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    var ctx = new AC();
    var buf = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
    var data = buf.getChannelData(0);
    for (var k = 0; k < data.length; k++) data[k] = Math.random() * 2 - 1;
    var fuente = ctx.createBufferSource(); fuente.buffer = buf; fuente.loop = true;
    var filtro = ctx.createBiquadFilter(); filtro.type = 'bandpass'; filtro.frequency.value = 1800; filtro.Q.value = .6;
    var gRuido = ctx.createGain(); gRuido.gain.value = 0;
    fuente.connect(filtro); filtro.connect(gRuido); gRuido.connect(ctx.destination); fuente.start();
    var tono = ctx.createOscillator(); tono.type = 'triangle'; tono.frequency.value = 523.25;
    var gTono = ctx.createGain(); gTono.gain.value = 0;
    tono.connect(gTono); gTono.connect(ctx.destination); tono.start();
    audio = { ctx: ctx, ruido: gRuido, tono: gTono };
    mezclar();
  }
  function mezclar() {
    if (!audio) return;
    var t = audio.ctx.currentTime;
    audio.ruido.gain.setTargetAtTime(encontrada ? 0.004 : 0.09 * (1 - fuerza) + 0.01, t, .05);
    audio.tono.gain.setTargetAtTime(encontrada ? 0.03 : 0.05 * Math.pow(fuerza, 3), t, .05);
  }
  btnSonido.addEventListener('click', function () {
    if (!audio) { prenderSonido(); btnSonido.setAttribute('aria-pressed', 'true'); btnSonido.textContent = '🔊 Sonido'; return; }
    var on = audio.ctx.state === 'running';
    if (on) audio.ctx.suspend(); else audio.ctx.resume();
    btnSonido.setAttribute('aria-pressed', String(!on));
    btnSonido.textContent = on ? '🔈 Sonido' : '🔊 Sonido';
  });

  function abrirChat() {
    chat.hidden = false;
    var src = (chat.getAttribute('data-cbox') || '').trim();
    if (src && !marco.querySelector('iframe')) {
      marco.innerHTML = '';
      var f = document.createElement('iframe');
      f.src = src; f.title = 'Chat de la radio pirata (Cbox)';
      f.width = '100%'; f.height = '420'; f.loading = 'lazy';
      f.setAttribute('allowtransparency', 'yes'); f.setAttribute('frameborder', '0');
      f.setAttribute('allow', 'autoplay');
      marco.appendChild(f);
    }
  }

  function sintonizar(final) {
    encontrada = true; fuerza = 1;
    radio.classList.add('radio--al-aire');
    estado.textContent = '▮ Señal encontrada: ' + objetivo.toFixed(1) + ' MHz';
    if (final) { guardar('leos-radio', hoy); if (window.leosLogro) window.leosLogro('radio'); }
    abrirChat(); pintar(); mezclar();
  }

  function pintar() {
    frec.textContent = Number(perilla.value).toFixed(1);
    var nivel = Math.round(fuerza * 5);
    for (var k = 0; k < barras.length; k++) barras[k].classList.toggle('on', k < nivel);
    if (!g || quieto) ruido();
  }

  function mover() {
    if (encontrada) { pintar(); return; }
    var f = Number(perilla.value);
    var dif = Math.abs(f - objetivo);
    fuerza = Math.max(0, 1 - dif / 5);
    clearTimeout(sostener);
    if (dif < 0.05) {
      estado.textContent = 'Algo se oye… no te muevas';
      sostener = setTimeout(function () { sintonizar(true); }, 900);
    } else if (fuerza > .75) estado.textContent = 'Ya casi…';
    else if (fuerza > .4) estado.textContent = 'Se oye algo entre la estática';
    else estado.textContent = 'Buscando señal…';
    pintar(); mezclar();
  }

  perilla.addEventListener('input', mover);
  if (leer('leos-radio') === hoy) {
    perilla.value = objetivo.toFixed(1);
    sintonizar(false);
    estado.textContent = '▮ Ya sintonizada hoy: ' + objetivo.toFixed(1) + ' MHz';
  } else {
    // Arranca en un lugar al azar, lejos del objetivo
    var inicio = objetivo > 98 ? 88.1 + 0.2 * (h % 20) : 107.9 - 0.2 * (h % 20);
    perilla.value = inicio.toFixed(1);
    mover();
  }
  if (g && !quieto) (function bucle() { ruido(); setTimeout(function () { requestAnimationFrame(bucle); }, 70); })();
})();

// Va en archivo aparte: la política de seguridad (CSP) de Neocities puede bloquear el JavaScript escrito dentro del HTML.

// Reproductor de Glass Ecosystem. Los datos (pistas, dónde vive el audio, enlaces) los escribe
// tools/music_sync.py desde music.json. Si el audio no carga, el reproductor lo dice y ofrece Spotify.
(function () {
  var player = document.querySelector('.player');
  var datos = document.getElementById('aero-data');
  if (!player || !datos) return;
  var cfg = JSON.parse(datos.textContent);
  var tracks = cfg.pistas || [];
  var title = document.getElementById('lcd-title');
  var time = document.getElementById('lcd-time');
  var fill = document.getElementById('seek-fill');
  var seek = document.getElementById('seek');
  var playBtn = player.querySelector('[data-act="play"]');
  var eject = player.querySelector('[data-act="eject"]');
  var items = player.querySelectorAll('#playlist button');
  var audio = new Audio();
  audio.preload = 'none';
  var cur = 0, cargada = -1;

  if (cfg.spotify) eject.hidden = false;

  function mmss(s) {
    s = Math.max(0, Math.floor(s || 0));
    return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
  }
  function setPlaying(on) {
    player.classList.toggle('is-playing', on);
    playBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    playBtn.textContent = on ? '❚❚' : '▶';
    playBtn.setAttribute('aria-label', on ? 'Pausar' : 'Reproducir');
  }
  function show(i) {
    cur = (i + tracks.length) % tracks.length;
    player.classList.remove('is-offline');
    title.textContent = (cur + 1) + '. ' + tracks[cur].t;
    time.textContent = mmss(0);
    fill.style.width = '0%';
    items.forEach(function (b, k) {
      if (k === cur) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current');
    });
  }
  function sinSenal() {
    setPlaying(false);
    player.classList.add('is-offline');
    title.textContent = cfg.spotify ? 'Sin señal. Pulsa ⏏ para oírlo en Spotify' : 'Sin señal por ahora';
  }
  function play() {
    if (!cfg.base) { sinSenal(); return; }
    if (cargada !== cur) { audio.src = cfg.base + tracks[cur].f; cargada = cur; }
    var p = audio.play();
    if (p && p.catch) p.catch(function (err) { if (err && err.name !== 'AbortError') sinSenal(); });
  }
  function stop() { audio.pause(); audio.currentTime = 0; setPlaying(false); fill.style.width = '0%'; time.textContent = mmss(0); }

  audio.addEventListener('playing', function () { setPlaying(true); });
  audio.addEventListener('pause', function () { setPlaying(false); });
  audio.addEventListener('error', sinSenal);
  audio.addEventListener('timeupdate', function () {
    time.textContent = mmss(audio.currentTime);
    if (audio.duration) fill.style.width = (audio.currentTime / audio.duration * 100) + '%';
  });
  audio.addEventListener('ended', function () {
    if (cur < tracks.length - 1) { show(cur + 1); play(); } else { stop(); show(0); }
  });
  seek.addEventListener('click', function (ev) {
    if (!audio.duration || cargada !== cur) return;
    var r = seek.getBoundingClientRect();
    audio.currentTime = (ev.clientX - r.left) / r.width * audio.duration;
  });

  player.addEventListener('click', function (ev) {
    var b = ev.target.closest('button');
    if (!b) return;
    if (b.dataset.i) { show(+b.dataset.i); play(); return; }
    var act = b.dataset.act;
    if (act === 'play') { if (audio.paused) play(); else audio.pause(); }
    if (act === 'stop') stop();
    if (act === 'next') { var on = !audio.paused; show(cur + 1); if (on) play(); }
    if (act === 'prev') { var on2 = !audio.paused; show(cur - 1); if (on2) play(); }
    if (act === 'eject' && cfg.spotify) { stop(); window.open(cfg.spotify, '_blank', 'noopener'); }
  });
  show(0);
})();

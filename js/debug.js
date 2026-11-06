// debug_room: palancas que afectan todo el sitio (leídas por estrellas.js) y la lista de logros.
(function () {
  function leer(k, def) { try { return JSON.parse(localStorage.getItem(k)) || def; } catch (e) { return def; } }
  function guardar(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }

  var flags = leer('leos-flags', {});
  document.querySelectorAll('[data-flag]').forEach(function (cb) {
    cb.checked = !!flags[cb.dataset.flag];
    cb.addEventListener('change', function () {
      flags[cb.dataset.flag] = cb.checked;
      guardar('leos-flags', flags);
      document.body.classList.toggle(cb.dataset.flag === 'noclip' ? 'noclip' : 'ver-estrellas', cb.checked);
    });
  });
  if (flags.noclip) document.body.classList.add('noclip');

  var reset = document.getElementById('d-reset');
  var msg = document.getElementById('d-reset-msg');
  reset.addEventListener('click', function () {
    guardar('leos-estrellas', []);
    msg.textContent = 'OK: las 8 estrellas volvieron a su lugar.';
    pintar();
  });

  function pintar() {
    var est = leer('leos-estrellas', []);
    var oob = leer('leos-oob', {});
    var L = [
      ['Juntar las 8 estrellas', est.length >= 8, est.length + '/8'],
      ['Entrar a test_room_00', !!oob.hub],
      ['Salir del bosque por el centro', !!oob.bosque_centro],
      ['Pisar glitch_city', !!oob.glitch],
      ['Leer el archivo de leyendas', !!oob.leyendas],
      ['Bajarte en una estación que no existe', !!oob.kisaragi],
      ['Sintonizar la radio pirata', !!oob.radio],
      ['Encontrar el debug_room', !!oob.debug]
    ];
    var ul = document.getElementById('d-logros');
    ul.innerHTML = '';
    L.forEach(function (l) {
      var li = document.createElement('li');
      li.className = l[1] ? 'ok' : '';
      li.textContent = (l[1] ? '[x] ' : '[ ] ') + l[0] + (l[2] ? ' (' + l[2] + ')' : '');
      ul.appendChild(li);
    });
  }
  pintar();
})();

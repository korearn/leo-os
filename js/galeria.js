// Visor de imágenes estilo Windows XP para las fotos de la galería (y de la portada).
// Sin JavaScript, cada foto sigue siendo un enlace normal a la imagen grande.
(function () {
  var fotos = Array.prototype.slice.call(document.querySelectorAll('a.shot__frame'));
  if (!fotos.length) return;
  var actual = 0;

  var visor = document.createElement('div');
  visor.className = 'visor';
  visor.hidden = true;
  visor.setAttribute('role', 'dialog');
  visor.setAttribute('aria-modal', 'true');
  visor.setAttribute('aria-labelledby', 'visor-titulo');
  visor.innerHTML =
    '<div class="visor__ventana">' +
      '<div class="visor__barra">' +
        '<span class="visor__icono" aria-hidden="true"></span>' +
        '<span class="visor__titulo" id="visor-titulo"></span>' +
        '<span class="visor__botones" aria-hidden="true"><i>_</i><i>□</i></span>' +
        '<button type="button" class="visor__cerrar" aria-label="Cerrar">×</button>' +
      '</div>' +
      '<div class="visor__lienzo"><img class="visor__img" alt=""></div>' +
      '<p class="visor__pie"></p>' +
      '<div class="visor__herramientas">' +
        '<button type="button" class="visor__btn" data-ir="-1" aria-label="Imagen anterior">◀</button>' +
        '<button type="button" class="visor__btn" data-ir="1" aria-label="Imagen siguiente">▶</button>' +
        '<span class="visor__sep" aria-hidden="true"></span>' +
        '<span class="visor__cuenta"></span>' +
      '</div>' +
    '</div>';
  document.body.appendChild(visor);

  var img = visor.querySelector('.visor__img');
  var titulo = visor.querySelector('.visor__titulo');
  var pie = visor.querySelector('.visor__pie');
  var cuenta = visor.querySelector('.visor__cuenta');
  var cerrarBtn = visor.querySelector('.visor__cerrar');
  var ultimoFoco = null;

  function mostrar(i) {
    actual = (i + fotos.length) % fotos.length;
    var a = fotos[actual];
    var mini = a.querySelector('img');
    var cap = a.closest('figure') && a.closest('figure').querySelector('figcaption');
    var archivo = a.getAttribute('href').split('/').pop();
    img.src = a.getAttribute('href');
    img.alt = mini ? mini.alt : '';
    titulo.textContent = archivo + ' - Visor de imágenes y fax de Windows';
    pie.textContent = (cap ? cap.textContent : '') + (mini && mini.alt ? ' · ' + mini.alt : '');
    cuenta.textContent = (actual + 1) + ' de ' + fotos.length;
  }
  function abrir(i) {
    ultimoFoco = document.activeElement;
    mostrar(i);
    visor.hidden = false;
    document.body.classList.add('con-visor');
    cerrarBtn.focus();
  }
  function cerrar() {
    visor.hidden = true;
    document.body.classList.remove('con-visor');
    if (ultimoFoco) ultimoFoco.focus();
  }

  fotos.forEach(function (a, i) {
    a.addEventListener('click', function (ev) {
      if (ev.ctrlKey || ev.metaKey || ev.shiftKey) return; // abrir en pestaña nueva sigue funcionando
      ev.preventDefault();
      abrir(i);
    });
  });
  visor.addEventListener('click', function (ev) {
    if (ev.target === visor) cerrar();
    var b = ev.target.closest('[data-ir]');
    if (b) mostrar(actual + Number(b.dataset.ir));
  });
  cerrarBtn.addEventListener('click', cerrar);
  document.addEventListener('keydown', function (ev) {
    if (visor.hidden) return;
    if (ev.key === 'Escape') cerrar();
    else if (ev.key === 'ArrowRight') mostrar(actual + 1);
    else if (ev.key === 'ArrowLeft') mostrar(actual - 1);
  });
})();

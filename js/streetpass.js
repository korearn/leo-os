// Tarjeta StreetPass (Sobre mí): cuenta cuántas veces se ha "cruzado" el visitante con LeOS.
// Un encuentro por día, guardado en el navegador del visitante (localStorage), como los encuentros de la 3DS.
(function () {
  var n = document.querySelector('.js-encuentros');
  var primero = document.querySelector('.js-primer-encuentro');
  if (!n) return;
  var hoy = new Date().toISOString().slice(0, 10);
  var datos;
  try { datos = JSON.parse(localStorage.getItem('leos-streetpass')) || {}; } catch (e) { datos = {}; }
  if (datos.ultimo !== hoy) {
    datos.veces = (datos.veces || 0) + 1;
    datos.ultimo = hoy;
    if (!datos.primero) datos.primero = hoy;
    try { localStorage.setItem('leos-streetpass', JSON.stringify(datos)); } catch (e) {}
  }
  var v = datos.veces || 1;
  n.textContent = v === 1 ? '1 vez (¡hola!)' : v + ' veces';
  if (primero && datos.primero) {
    var p = datos.primero.split('-');
    primero.textContent = p[2] + '/' + p[1] + '/' + p[0];
  }
})();

// Zona "fuera de los límites": recuerda qué cuartos visitó el visitante (para los logros del debug_room).
(function () {
  var zona = document.body.getAttribute('data-zona');
  if (!zona) return;
  try {
    var v = JSON.parse(localStorage.getItem('leos-oob')) || {};
    if (!v[zona]) { v[zona] = true; localStorage.setItem('leos-oob', JSON.stringify(v)); }
  } catch (e) {}
})();

// Para que otras páginas de la zona marquen logros especiales (p. ej. salir del bosque).
window.leosLogro = function (clave) {
  try {
    var v = JSON.parse(localStorage.getItem('leos-oob')) || {};
    v[clave] = true;
    localStorage.setItem('leos-oob', JSON.stringify(v));
  } catch (e) {}
};

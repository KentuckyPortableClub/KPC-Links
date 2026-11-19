/* KPC Logger beta on the website: runs in <head> BEFORE the app's scripts (Lounge round stage 2, Nov 18 2026).
   Switches that stay off on the website (KPC owner: no auto spot me on the website; AUTO run / hunt / both stay off;
   the level helper and 'hear my processed voice' are app only for now). It only turns saved switches off; kpc-web.css hides
   their buttons, so they can't be turned back on here. Nothing else is changed. */
(function () {
  'use strict';
  window.KPC_WEB = true;
  function off(k, f) { try { var o = JSON.parse(localStorage.getItem(k) || '{}') || {}; if (f(o)) localStorage.setItem(k, JSON.stringify(o)); } catch (e) {} }
  off('kpcAppAutoSpot', function (o) { if (o.ask === false) return false; o.ask = false; return true; });
  off('kpcAppDigi', function (o) { if (o.showAuto === false) return false; o.showAuto = false; return true; });
  off('kpcApp', function (o) { if (!o.vmon) return false; o.vmon = false; return true; });
})();

/* KPC translate button (Oct 28, chat 1; Brandon Oct 27 10:23 PM 'yes eventually').
   Opens the current page through Google Translate. No translated copies of the
   site are kept — this is just a proxy link, same idea as the Compare page notes. */
(function () {
  function openTranslate() {
    var lang = ((navigator.language || navigator.userLanguage || 'en') + '').split('-')[0].toLowerCase();
    if (lang === 'en') lang = 'es'; // translating an English page to English does nothing useful
    var url = 'https://translate.google.com/translate?sl=auto&tl=' + encodeURIComponent(lang) + '&u=' + encodeURIComponent(location.href);
    window.open(url, '_blank', 'noopener');
  }
  var btns = document.querySelectorAll('.nav-translate');
  for (var i = 0; i < btns.length; i++) {
    btns[i].addEventListener('click', function (e) { e.preventDefault(); openTranslate(); });
  }
})();

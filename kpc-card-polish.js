/* Park cards above the map overlays (Nov 8 2026; Brandon: 'make sure cards pop up over stuff', keep every feature).
   Every Leaflet map on the page: a card opens fully in view (auto-pan with room for the controls, height fits the map, scrolls
   inside if long) and any control, legend or layer box it would cover steps back until the card closes. Page options win. */
(function(){
 if(!window.L||!L.Map||L.Map._kpcCardPolish)return; L.Map._kpcCardPolish=1;
 var OVER='.leaflet-control, .kx-docked, .gis-controls, .pl-banner, [data-kxlegend]';
 function hit(a,b){return a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top}
 function host(map){var c=map.getContainer();return c.closest('.mapwrap, .pl-mapwrap, .usp-mapwrap, section, main')||c.parentNode||c}
 function clear(map){(map._kpcUnder||[]).forEach(function(el){el.classList.remove('kpc-under-card')});map._kpcUnder=[]}
 function cover(map,pop){
  clear(map); var el=pop&&pop.getElement&&pop.getElement(); if(!el||!map._loaded)return;
  var r=el.getBoundingClientRect(); if(!r.width)return;
  var all=[].slice.call(host(map).querySelectorAll(OVER)).filter(function(o){return !el.contains(o)&&!o.contains(el)});
  all.forEach(function(o){if(o.offsetParent!==null&&hit(r,o.getBoundingClientRect())){o.classList.add('kpc-under-card');map._kpcUnder.push(o)}});
 }
 function fit(map,pop){
  try{
   var sz=map.getSize(), o=pop.options, mh=Math.max(140,sz.y-(sz.x<600?150:90));
   if(!o.maxHeight||o.maxHeight>mh){o.maxHeight=mh}
   var room=sz.x-(sz.x<600?76:110); if(!o.maxWidth||o.maxWidth>room){o.maxWidth=Math.max(170,room)}
   if(o.minWidth>o.maxWidth){o.minWidth=o.maxWidth}
   if(!o.autoPanPaddingTopLeft)o.autoPanPaddingTopLeft=L.point(sz.x<600?10:54,sz.x<600?60:14);
   if(!o.autoPanPaddingBottomRight)o.autoPanPaddingBottomRight=L.point(sz.x<600?10:20,sz.x<600?40:20);
   o.autoPan=true; pop.update();
  }catch(e){}
 }
 L.Map.addInitHook(function(){
  var map=this;
  map.on('popupopen',function(e){var p=e.popup;fit(map,p);setTimeout(function(){fit(map,p);if(p._map)p._adjustPan&&p._adjustPan()},0);setTimeout(function(){cover(map,p)},30);map.once('moveend',function(){if(p.isOpen&&p.isOpen())cover(map,p)})});
  map.on('popupclose',function(){clear(map)});
  map.on('zoomend moveend resize',function(){var p=map._popup;if(p&&p.isOpen&&p.isOpen())cover(map,p);else clear(map)});
 });
})();

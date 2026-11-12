/* Nov 11 (page-size PR): a small WORKING stand-in for Leaflet 1.9.4, for headless tests only (the CDN is not reachable
   in the sandbox and tests must not touch the network). It keeps real map state (centre, zoom, bounds of an 800x600 view),
   real layer add / remove with 'add' / 'remove' / 'layeradd' / 'moveend' / 'zoomend' events, panes and controls. Anything
   it does not know returns a harmless chainable no-op, so page code that draws (popups, styles, tiles) just runs. */
(function () {
  'use strict';
  const noop = function () { return NOOP; };
  const NOOP = new Proxy(noop, { get(t, k) { if (k === 'then') return undefined; if (k === Symbol.toPrimitive) return () => ''; if (k === 'length') return 0; return NOOP; }, apply() { return NOOP; }, construct() { return NOOP; } });
  const CLS = () => { const proto = Object.create(Layer.prototype); return { addInitHook() {}, include(p) { Object.assign(proto, p); }, mergeOptions() {}, extend: p => extendLayer(p), prototype: proto }; };   /* own prototype: a page patching L.CircleMarker.prototype does not change every layer */
  const soft = o => new Proxy(o, { get(t, k) { if (k in t) return t[k]; if (typeof k === 'symbol' || k === 'then' || k === 'toJSON' || String(k)[0] === '_') return undefined; if (/^[A-Z]/.test(k)) return (t[k] = CLS()); return noop; } });
  function Ev() {}
  Ev.prototype.on = function (types, fn, ctx) { if (typeof types === 'object') { for (const k in types) this.on(k, types[k], fn); return this; } (this._ev = this._ev || []); String(types).split(/\s+/).forEach(t => t && this._ev.push([t, fn, ctx, false])); return this; };
  Ev.prototype.once = function (types, fn, ctx) { (this._ev = this._ev || []); String(types).split(/\s+/).forEach(t => t && this._ev.push([t, fn, ctx, true])); return this; };
  Ev.prototype.off = function (types, fn) { if (!this._ev) return this; if (!types) { this._ev = []; return this; } const ts = String(types).split(/\s+/); this._ev = this._ev.filter(e => !(ts.includes(e[0]) && (!fn || e[1] === fn))); return this; };
  Ev.prototype.fire = function (t, data) { const e = Object.assign({ type: t, target: this }, data || {}); (this._ev || []).slice().forEach(x => { if (x[0] !== t) return; if (x[3]) this._ev = this._ev.filter(y => y !== x); try { x[1].call(x[2] || this, e); } catch (err) { setTimeout(() => { throw err; }); } }); return this; };
  Ev.prototype.listens = function (t) { return !!(this._ev || []).some(e => e[0] === t); };
  function LatLng(a, b) { if (Array.isArray(a)) { b = a[1]; a = a[0]; } else if (a && typeof a === 'object') { b = a.lng != null ? a.lng : a.lon; a = a.lat; } this.lat = +a; this.lng = +b; }
  LatLng.prototype.equals = function (o) { o = ll(o); return o.lat === this.lat && o.lng === this.lng; };
  LatLng.prototype.distanceTo = function (o) { o = ll(o); const r = Math.PI / 180, d = 6371e3 * 2 * Math.asin(Math.sqrt(Math.sin((o.lat - this.lat) * r / 2) ** 2 + Math.cos(this.lat * r) * Math.cos(o.lat * r) * Math.sin((o.lng - this.lng) * r / 2) ** 2)); return d; };
  const ll = (a, b) => a instanceof LatLng ? a : new LatLng(a, b);
  function Bounds(a, b) { this._s = 90; this._w = 180; this._n = -90; this._e = -180; this._ok = false; if (a) { if (Array.isArray(a) && !Array.isArray(b) && Array.isArray(a[0])) a.forEach(p => this.extend(p)); else if (Array.isArray(a) && typeof a[0] === 'object' && !(a[0] instanceof Array)) a.forEach(p => this.extend(p)); else { this.extend(a); if (b) this.extend(b); } } }
  Bounds.prototype.extend = function (p) { if (p instanceof Bounds) { if (p._ok) { this.extend([p._s, p._w]); this.extend([p._n, p._e]); } return this; } const q = ll(p); if (!isFinite(q.lat) || !isFinite(q.lng)) return this; this._s = Math.min(this._s, q.lat); this._n = Math.max(this._n, q.lat); this._w = Math.min(this._w, q.lng); this._e = Math.max(this._e, q.lng); this._ok = true; return this; };
  Bounds.prototype.getSouth = function () { return this._s; }; Bounds.prototype.getNorth = function () { return this._n; };
  Bounds.prototype.getWest = function () { return this._w; }; Bounds.prototype.getEast = function () { return this._e; };
  Bounds.prototype.getSouthWest = function () { return ll(this._s, this._w); }; Bounds.prototype.getNorthEast = function () { return ll(this._n, this._e); };
  Bounds.prototype.getCenter = function () { return ll((this._s + this._n) / 2, (this._w + this._e) / 2); };
  Bounds.prototype.isValid = function () { return this._ok; };
  Bounds.prototype.pad = function (r) { const h = (this._n - this._s) * r, w = (this._e - this._w) * r; return new Bounds([this._s - h, this._w - w], [this._n + h, this._e + w]); };
  Bounds.prototype.contains = function (p) { if (p instanceof Bounds) return this.contains([p._s, p._w]) && this.contains([p._n, p._e]); const q = ll(p); return q.lat >= this._s && q.lat <= this._n && q.lng >= this._w && q.lng <= this._e; };
  Bounds.prototype.intersects = function (b) { b = b instanceof Bounds ? b : new Bounds(b); return !(b._s > this._n || b._n < this._s || b._w > this._e || b._e < this._w); };
  Bounds.prototype.toBBoxString = function () { return [this._w, this._s, this._e, this._n].join(','); };
  function Layer(data, opts) { this._data = data; this.options = Object.assign({}, opts || {}); this._layers = []; this._map = null; this.feature = null; }
  Layer.prototype = Object.create(Ev.prototype);
  Layer.prototype.addTo = function (m) { m.addLayer(this); return this; };
  Layer.prototype.remove = function () { if (this._map) this._map.removeLayer(this); return this; };
  Layer.prototype.onAdd = function () {}; Layer.prototype.onRemove = function () {};
  Layer.prototype.bindPopup = function (c, o) { this._popup = (c instanceof Popup) ? c : new Popup(o).setContent(c); return this; };
  Layer.prototype.getPopup = function () { return this._popup || null; };
  Layer.prototype.openPopup = function () { if (this._popup && this._map) { this._popup._src = this; this._map.openPopup(this._popup); } return this; };
  Layer.prototype.closePopup = function () { if (this._map) this._map.closePopup(); return this; };
  Layer.prototype.isPopupOpen = function () { return !!(this._popup && this._map && this._map._popup === this._popup); };
  Layer.prototype.setPopupContent = function (c) { if (this._popup) this._popup.setContent(c); return this; };
  Layer.prototype.bindTooltip = function () { return this; }; Layer.prototype.unbindTooltip = function () { return this; }; Layer.prototype.openTooltip = function () { return this; }; Layer.prototype.closeTooltip = function () { return this; };
  Layer.prototype.setStyle = function (s) { this._style = s; this._layers.forEach(l => l.setStyle && l.setStyle(s)); return this; };
  Layer.prototype.bringToBack = function () { return this; }; Layer.prototype.bringToFront = function () { return this; };
  Layer.prototype.setZIndex = function () { return this; }; Layer.prototype.setOpacity = function () { return this; }; Layer.prototype.redraw = function () { return this; };
  Layer.prototype.addLayer = function (l) { if (!this._layers.includes(l)) this._layers.push(l); if (this._map && !this._map.hasLayer(l)) this._map.addLayer(l); return this; };
  Layer.prototype.removeLayer = function (l) { this._layers = this._layers.filter(x => x !== l); if (this._map && this._map.hasLayer(l)) this._map.removeLayer(l); return this; };
  Layer.prototype.clearLayers = function () { this._layers.slice().forEach(l => this.removeLayer(l)); return this; };
  Layer.prototype.eachLayer = function (fn, ctx) { this._layers.slice().forEach(l => fn.call(ctx, l)); return this; };
  Layer.prototype.getLayers = function () { return this._layers.slice(); };
  Layer.prototype.hasLayer = function (l) { return this._layers.includes(l); };
  Layer.prototype.setLatLng = function (p) { this._ll = ll(p); return this; }; Layer.prototype.getLatLng = function () { return this._ll; };
  Layer.prototype.setLatLngs = function (p) { this._lls = p; return this; }; Layer.prototype.getLatLngs = function () { return this._lls || []; };
  Layer.prototype.setRadius = function () { return this; }; Layer.prototype.setIcon = function () { return this; }; Layer.prototype.setUrl = function () { return this; };
  Layer.prototype.getElement = function () { return null; }; Layer.prototype.getContainer = function () { return null; };
  Layer.prototype.toGeoJSON = function () { return this._data || { type: 'FeatureCollection', features: [] }; };
  Layer.prototype.getBounds = function () { const b = new Bounds(); if (this._ll) b.extend(this._ll); (this._lls || []).forEach(p => { if (Array.isArray(p) && Array.isArray(p[0])) p.forEach(q => b.extend(q)); else b.extend(p); }); this._layers.forEach(l => { if (l.getBounds) { const x = l.getBounds(); if (x && x.isValid && x.isValid()) b.extend(x); } }); if (this._radius && this._ll) { const d = this._radius / 111320; b.extend([this._ll.lat - d, this._ll.lng - d]); b.extend([this._ll.lat + d, this._ll.lng + d]); } return b; };
  Layer.prototype.addData = function (d) { geo(this, d); return this; };
  function geo(group, d) { const fs = !d ? [] : d.type === 'FeatureCollection' ? d.features || [] : Array.isArray(d) ? d : [d]; const o = group.options; fs.forEach(f => { const l = new Layer(f, {}); l.feature = f; if (o.style) l.setStyle(typeof o.style === 'function' ? o.style(f) : o.style); if (o.onEachFeature) o.onEachFeature(f, l); group.addLayer(l); }); }
  const wrap = l => soft(l);
  function Popup(o) { Layer.call(this, null, o); }
  Popup.prototype = Object.create(Layer.prototype);
  Popup.prototype.setContent = function (c) { this._content = c; return this; };
  Popup.prototype.getContent = function () { return this._content; };
  Popup.prototype.openOn = function (m) { m.openPopup(this); return this; };
  Popup.prototype.update = function () { return this; }; Popup.prototype._updateLayout = function () {}; Popup.prototype._updatePosition = function () {}; Popup.prototype._adjustPan = function () {};
  Popup.prototype.isOpen = function () { return !!(this._map && this._map._popup === this); };
  function MapObj(el, opts) {
    this._c = typeof el === 'string' ? document.getElementById(el) : el; this.options = Object.assign({ minZoom: 0, maxZoom: 19 }, opts || {});
    this._layers = []; this._panes = {}; this._center = ll(0, 0); this._zoom = 0; this._popup = null; this._loaded = false;
    if (this._c) { this._c.classList.add('leaflet-container'); this._mapPane = document.createElement('div'); this._mapPane.className = 'leaflet-map-pane'; this._c.appendChild(this._mapPane); this._ctl = document.createElement('div'); this._ctl.className = 'leaflet-control-container'; this._c.appendChild(this._ctl); }
    ['mapPane', 'tilePane', 'overlayPane', 'shadowPane', 'markerPane', 'tooltipPane', 'popupPane'].forEach(n => this.createPane(n));
    window.__lsMaps = (window.__lsMaps || []).concat(this);
    if (this.options.center && this.options.zoom != null) this.setView(this.options.center, this.options.zoom);
  }
  MapObj.prototype = Object.create(Ev.prototype);
  MapObj.prototype.getContainer = function () { return this._c; };
  MapObj.prototype.createPane = function (n) { if (this._panes[n]) return this._panes[n]; const d = document.createElement('div'); d.className = 'leaflet-pane leaflet-' + n; if (this._mapPane) this._mapPane.appendChild(d); this._panes[n] = d; return d; };
  MapObj.prototype.getPane = function (n) { return typeof n === 'string' ? this._panes[n] : n; };
  MapObj.prototype.getPanes = function () { return this._panes; };
  MapObj.prototype._move = function (c, z) { const zc = z !== this._zoom; this._center = ll(c); this._zoom = Math.max(this.options.minZoom || 0, Math.min(this.options.maxZoom || 19, z)); const first = !this._loaded; this._loaded = true; if (first) this.fire('load'); this.fire('move'); if (zc || first) this.fire('zoomend'); this.fire('moveend'); };
  MapObj.prototype.setView = function (c, z) { this._move(c, z == null ? this._zoom : z); return this; };
  MapObj.prototype.flyTo = MapObj.prototype.setView;
  MapObj.prototype.panTo = function (c) { return this.setView(c, this._zoom); };
  MapObj.prototype.setZoom = function (z) { return this.setView(this._center, z); };
  MapObj.prototype.zoomIn = function () { return this.setZoom(this._zoom + 1); }; MapObj.prototype.zoomOut = function () { return this.setZoom(this._zoom - 1); };
  MapObj.prototype.getCenter = function () { return ll(this._center.lat, this._center.lng); };
  MapObj.prototype.getZoom = function () { return this._zoom; };
  MapObj.prototype.getMaxZoom = function () { return this.options.maxZoom; }; MapObj.prototype.getMinZoom = function () { return this.options.minZoom || 0; };
  MapObj.prototype.getSize = function () { return point(800, 600); };
  MapObj.prototype._dpp = function () { return 360 / (256 * Math.pow(2, this._zoom)); };
  MapObj.prototype.getBounds = function () { const d = this._dpp(), c = this._center, k = Math.max(.2, Math.cos(c.lat * Math.PI / 180)); return new Bounds([c.lat - 300 * d * k, c.lng - 400 * d], [c.lat + 300 * d * k, c.lng + 400 * d]); };
  MapObj.prototype.getBoundsZoom = function (b) { b = b instanceof Bounds ? b : new Bounds(b); if (!b.isValid()) return this._zoom; const w = Math.max(1e-9, b._e - b._w), h = Math.max(1e-9, (b._n - b._s) / Math.max(.2, Math.cos(b.getCenter().lat * Math.PI / 180))); const z = Math.floor(Math.min(Math.log2(800 * 360 / 256 / w), Math.log2(600 * 360 / 256 / h))); return Math.max(0, Math.min(this.options.maxZoom || 19, z)); };
  MapObj.prototype.fitBounds = function (b, o) { b = b instanceof Bounds ? b : new Bounds(b); if (!b.isValid()) return this; let z = this.getBoundsZoom(b); if (o && o.maxZoom != null) z = Math.min(z, o.maxZoom); return this.setView(b.getCenter(), z); };
  MapObj.prototype.flyToBounds = MapObj.prototype.fitBounds;
  MapObj.prototype.invalidateSize = function () { return this; };
  MapObj.prototype.whenReady = function (fn, ctx) { if (this._loaded) setTimeout(() => fn.call(ctx || this, { target: this }), 0); else this.once('load', fn, ctx); return this; };
  MapObj.prototype.addLayer = function (l) { if (!l) return this; if (this._layers.includes(l)) return this; this._layers.push(l); l._map = this; try { l.onAdd && l.onAdd(this); } catch (e) {} (l._layers || []).forEach(x => this.addLayer(x)); if (l.fire) l.fire('add'); this.fire('layeradd', { layer: l }); return this; };
  MapObj.prototype.removeLayer = function (l) { if (!l || !this._layers.includes(l)) return this; this._layers = this._layers.filter(x => x !== l); (l._layers || []).forEach(x => this.removeLayer(x)); l._map = null; if (l.fire) l.fire('remove'); this.fire('layerremove', { layer: l }); if (this._popup === l) this._popup = null; return this; };
  MapObj.prototype.hasLayer = function (l) { return this._layers.includes(l); };
  MapObj.prototype.eachLayer = function (fn, ctx) { this._layers.slice().forEach(l => fn.call(ctx, l)); return this; };
  MapObj.prototype.openPopup = function (p, latlng) { if (!(p instanceof Popup)) { p = new Popup().setContent(p); } if (latlng) p.setLatLng(latlng); if (this._popup) this.closePopup(); this._popup = p; this.addLayer(p); this.fire('popupopen', { popup: p }); if (p._src) p._src.fire('popupopen', { popup: p }); return this; };
  MapObj.prototype.closePopup = function () { const p = this._popup; if (!p) return this; this._popup = null; this.removeLayer(p); this.fire('popupclose', { popup: p }); if (p._src) p._src.fire('popupclose', { popup: p }); return this; };
  MapObj.prototype.latLngToContainerPoint = function (p) { p = ll(p); const d = this._dpp(); return point(400 + (p.lng - this._center.lng) / d, 300 - (p.lat - this._center.lat) / d); };
  MapObj.prototype.containerPointToLatLng = function (p) { const d = this._dpp(); return ll(this._center.lat - (p.y - 300) * d, this._center.lng + (p.x - 400) * d); };
  MapObj.prototype.latLngToLayerPoint = MapObj.prototype.latLngToContainerPoint; MapObj.prototype.layerPointToLatLng = MapObj.prototype.containerPointToLatLng;
  MapObj.prototype.project = function (p) { return this.latLngToContainerPoint(p); }; MapObj.prototype.unproject = function (p) { return this.containerPointToLatLng(p); };
  MapObj.prototype.mouseEventToLatLng = function () { return this.getCenter(); };
  MapObj.prototype.locate = function () { return this; }; MapObj.prototype.stopLocate = function () { return this; };
  MapObj.prototype.addControl = function (c) { c.addTo(this); return this; }; MapObj.prototype.removeControl = function (c) { c.remove(); return this; };
  MapObj.prototype.remove = function () { this._layers.slice().forEach(l => this.removeLayer(l)); return this; };
  ['dragging', 'touchZoom', 'doubleClickZoom', 'scrollWheelZoom', 'boxZoom', 'keyboard', 'tap', 'attributionControl', 'zoomControl'].forEach(k => { MapObj.prototype[k] = { enable() {}, disable() {}, enabled() { return true; }, setPrefix() { return this; }, addAttribution() { return this; }, setPosition() { return this; }, remove() {} }; });
  function point(x, y) { if (Array.isArray(x)) { y = x[1]; x = x[0]; } return { x: +x, y: +y, add(o) { return point(this.x + o.x, this.y + o.y); }, subtract(o) { return point(this.x - o.x, this.y - o.y); }, divideBy(n) { return point(this.x / n, this.y / n); }, multiplyBy(n) { return point(this.x * n, this.y * n); }, round() { return this; }, distanceTo(o) { return Math.hypot(this.x - o.x, this.y - o.y); } }; }
  function Control(o) { this.options = Object.assign({ position: 'topright' }, o || {}); }
  Control.prototype.addTo = function (m) { this._map = m; let el = null; try { el = this.onAdd ? this.onAdd(m) : null; } catch (e) { setTimeout(() => { throw e; }); } if (!el) el = document.createElement('div'); this._container = el; if (m._ctl) m._ctl.appendChild(el); return this; };
  Control.prototype.remove = function () { if (this._container && this._container.parentNode) this._container.parentNode.removeChild(this._container); try { this.onRemove && this.onRemove(this._map); } catch (e) {} this._map = null; return this; };
  Control.prototype.getContainer = function () { return this._container; };
  Control.prototype.setPosition = function () { return this; };
  Control.prototype.addBaseLayer = function () { return this; }; Control.prototype.addOverlay = function () { return this; }; Control.prototype.removeLayer = function () { return this; };
  Control.prototype.expand = function () { return this; }; Control.prototype.collapse = function () { return this; };
  Control.extend = function (proto) { function C(o) { Control.call(this, Object.assign({}, proto.options || {}, o || {})); if (this.initialize) this.initialize.apply(this, arguments); } C.prototype = Object.create(Control.prototype); Object.assign(C.prototype, proto); return C; };
  const control = function (o) { return new Control(o); };
  control.layers = function () { return new Control(); }; control.scale = function () { return new Control(); }; control.zoom = function () { return new Control(); }; control.attribution = function () { return new Control(); };
  function extendLayer(proto) { function C(a, b) { Layer.call(this, null, Object.assign({}, proto.options || {}, (b && typeof b === 'object') ? b : (a && typeof a === 'object' && !Array.isArray(a) ? a : {}))); if (this.initialize) this.initialize.apply(this, arguments); } C.prototype = Object.create(Layer.prototype); Object.assign(C.prototype, proto); C.extend = p2 => { const D = extendLayer(Object.assign({}, proto, p2)); return D; }; C.include = p2 => Object.assign(C.prototype, p2); return C; }
  const DomUtil = soft({ create(tag, cls, parent) { const e = document.createElement(tag); if (cls) e.className = cls; if (parent) parent.appendChild(e); return e; }, addClass(e, c) { e && e.classList.add(...String(c).split(/\s+/).filter(Boolean)); }, removeClass(e, c) { e && e.classList.remove(...String(c).split(/\s+/).filter(Boolean)); }, hasClass(e, c) { return !!(e && e.classList.contains(c)); }, toggleClass(e, c) { e && e.classList.toggle(c); }, remove(e) { e && e.parentNode && e.parentNode.removeChild(e); }, get(id) { return typeof id === 'string' ? document.getElementById(id) : id; }, setPosition() {}, empty(e) { if (e) e.innerHTML = ''; } });
  const DomEvent = soft({ on(el, t, fn) { if (el && el.addEventListener) String(t).split(/\s+/).forEach(x => x && el.addEventListener(x, fn)); return DomEvent; }, off(el, t, fn) { if (el && el.removeEventListener) String(t).split(/\s+/).forEach(x => x && el.removeEventListener(x, fn)); return DomEvent; }, stop(e) { if (e && e.preventDefault) e.preventDefault(); if (e && e.stopPropagation) e.stopPropagation(); return DomEvent; }, preventDefault(e) { if (e && e.preventDefault) e.preventDefault(); return DomEvent; }, stopPropagation(e) { if (e && e.stopPropagation) e.stopPropagation(); return DomEvent; }, disableClickPropagation() { return DomEvent; }, disableScrollPropagation() { return DomEvent; } });
  const mk = (data, o, extra) => { const l = new Layer(data, o); if (extra) extra(l); return wrap(l); };
  const L = {
    version: '1.9.4-test-standin',
    map: (el, o) => wrap(new MapObj(el, o)),
    latLng: (a, b) => ll(a, b), latLngBounds: (a, b) => new Bounds(a, b), point, bounds: () => NOOP,
    tileLayer: Object.assign((u, o) => mk(null, Object.assign({ url: u }, o)), { wms: (u, o) => mk(null, o) }),
    layerGroup: (ls, o) => mk(null, o, l => (ls || []).forEach(x => l.addLayer(x))),
    featureGroup: (ls, o) => mk(null, o, l => (ls || []).forEach(x => l.addLayer(x))),
    geoJSON: (d, o) => mk(d, o, l => geo(l, d)), geoJson: (d, o) => mk(d, o, l => geo(l, d)),
    circleMarker: (p, o) => mk(null, o, l => l.setLatLng(p)), marker: (p, o) => mk(null, o, l => l.setLatLng(p)),
    circle: (p, o) => mk(null, o, l => { l.setLatLng(p); l._radius = (o && o.radius) || 0; }),
    polyline: (p, o) => mk(null, o, l => l.setLatLngs(p)), polygon: (p, o) => mk(null, o, l => l.setLatLngs(p)), rectangle: (p, o) => mk(null, o, l => l.setLatLngs(p)),
    imageOverlay: (u, b, o) => mk(null, o), videoOverlay: (u, b, o) => mk(null, o),
    popup: o => new Popup(o), tooltip: o => mk(null, o),
    divIcon: o => ({ options: o || {} }), icon: o => ({ options: o || {} }),
    svg: o => mk(null, o), canvas: o => mk(null, o),
    control, Control, DomUtil, DomEvent,
    Layer: { extend: extendLayer }, GridLayer: { extend: extendLayer }, TileLayer: { extend: extendLayer }, Path: { extend: extendLayer, prototype: { setStyle: function (st) { return Layer.prototype.setStyle.call(this, st); } } }, Polyline: { extend: extendLayer },
    Class: { extend: p => { function C() { if (this.initialize) this.initialize.apply(this, arguments); } Object.assign(C.prototype, p); return C; } },
    Handler: { extend: p => { function C(m) { this._map = m; } Object.assign(C.prototype, { enable() {}, disable() {} }, p); return C; } },
    Map: { addInitHook() {}, include(p) { Object.assign(MapObj.prototype, p); }, mergeOptions() {} },
    Icon: { Default: { imagePath: '', mergeOptions() {} }, extend: p => function () { return { options: p }; } },
    Marker: { prototype: Layer.prototype, include(p) { Object.assign(Layer.prototype, p); } },
    Browser: { mobile: false, touch: false, retina: false, android: false, ie: false },
    Util: soft({ extend: Object.assign, bind: (f, o) => f.bind(o), stamp: o => o._leaflet_id || (o._leaflet_id = ++L.__id), setOptions: (o, x) => (o.options = Object.assign({}, o.options, x)), template: (s, d) => String(s).replace(/\{ *([\w_ -]+) *\}/g, (m, k) => d[k] == null ? '' : d[k]), requestAnimFrame: f => requestAnimationFrame(f), cancelAnimFrame: () => {} }),
    CRS: { EPSG3857: NOOP, EPSG4326: NOOP, Simple: NOOP }, Projection: NOOP, __id: 0,
    noConflict() { return L; }
  };
  window.L = soft(L);
})();

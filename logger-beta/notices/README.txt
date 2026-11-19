KPC app: notices for the parts made by other people
=====================================================

The KPC app is made by the Kentucky Portable Club. A few parts inside it were
made by other people and are used under their own licences. Those licences ask
that this notice travels with the app, so it lives here, inside the app's own
files (www/notices/), on Android, Windows and the iPhone page alike.


1. ft8_lib  (the FT8 / FT4 decoder and encoder)
   -------------------------------------------
   By Karlis Goba. MIT licence.
   Full text: ft8_lib-MIT.txt in this folder.
   Source:    https://github.com/kgoba/ft8_lib
   In the app: kpc-ft8.wasm and kpc-ft8-wasm.js (built by tools/ft8/build.sh,
   with the small changes listed in that script).


2. codec2 / FreeDV  (digital voice: FreeDV 700D, 700E and 1600)
   ------------------------------------------------------------
   By David Rowe and the FreeDV project. GNU Lesser General Public Licence,
   version 2.1 (LGPL-2.1).
   Full text: codec2-LGPL-2.1.txt in this folder.
   Source:    https://github.com/drowe67/codec2
              built from commit 310777b1c6f1af0bc7c72f5b32f80f6fd9136962
              (version 1.2.0, March 17 2026)
   In the app: kpc-dv.wasm and kpc-dv-wasm.js, a separate library that the
   app's own code (kpc-dv.js) only loads and calls.
   Your rights under the LGPL: you may get codec2's source from the address
   above, change it, rebuild the library, and put your own build in place of
   ours. How to rebuild, the exact file list, and the one small change made at
   build time are written in tools/dv/README.md in the KPC app's source. To put
   in your own build, replace both kpc-dv.wasm and kpc-dv-wasm.js in the app's
   www folder (in the Windows app that folder is inside "resources"). The club
   will also send that README and build script to anyone who asks.


3. Natural Earth  (the built-in world map that works with no signal)
   -----------------------------------------------------------------
   Made with Natural Earth. Free vector and raster map data
   @ naturalearthdata.com.
   Natural Earth data is in the public domain. No permission is needed to use
   it; this credit is given as a thank-you.
   In the app: kpc-world.js (1:110m land and country borders, 1:50m state and
   province lines, rounded to 0.05 degrees).


Other things the app uses
-------------------------
- The Windows app is built with Electron (MIT). Electron and Chromium put their
  own licence files next to the program when it is installed
  (LICENSE.electron.txt and LICENSES.chromium.html).
- The Windows app's remote link uses the "ws" package (MIT); its licence file
  ships inside the app with the package.
- The Android app is built with Capacitor (MIT). It talks to USB radios with
  usb-serial-for-android (MIT, https://github.com/mik3y/usb-serial-for-android).
- Satellite map pictures come from Esri World Imagery (or USGS) over the
  internet and are credited on the map whenever they show. They are not stored
  in the app.
- The TOPO map pictures come from USGS The National Map (the USGSTopo map,
  https://basemap.nationalmap.gov), over the internet. They are a work of the
  US government and in the public domain; the map says "Topo map: USGS The
  National Map" whenever they show, as a thank-you. They are not stored in the
  app, so the topo map needs a signal; with none, the built-in map shows.
- Contest helper files (CTY.DAT from country-files.com, MASTER.SCP from
  supercheckpartial.com) are not part of the app. The app only downloads them
  when you press the button for them.

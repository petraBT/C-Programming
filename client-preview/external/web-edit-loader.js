// Loads both of the web-edit target's footer scripts.
//
// PreTeXt's html.js.extra stringparam takes exactly one file - "A place to put
// *one* Javascript file at the *end* of an HTML page", per the extra-js-footer
// template in pretext-html.xsl. (html.css.extra tokenizes on ", " and takes a
// list; the JS one does not.) The web-edit target needs two: classroom.js,
// inherited from the web-client target it mirrors, and ptx-edit.js, the
// authoring helper. Hence this shim.
//
// Only web-edit uses it. web-client still points html.js.extra straight at
// classroom.js, so nothing about the deployed build changes.
(function () {
  'use strict'

  // Resolve siblings relative to this file's own URL rather than hard-coding
  // "external/", so the pages nested in subdirectories load them too.
  var self = document.currentScript && document.currentScript.src
  var base = self ? self.replace(/[^/]*$/, '') : 'external/'

  ;['classroom.js', 'ptx-edit.js'].forEach(function (name) {
    var script = document.createElement('script')
    script.src = base + name
    // Dynamically inserted scripts default to async, which would let these two
    // execute in either order. They are independent today, but ordered
    // execution is the cheaper thing to guarantee than to remember.
    script.async = false
    document.head.appendChild(script)
  })
})()

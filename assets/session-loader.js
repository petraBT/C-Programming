// Loads the two scripts the web-client target needs on every book page: course.js (the
// per-course settings) and then classroom.js (the shared session client, which reads them).
// PreTeXt's html.js.extra takes exactly one file, hence this shim; web-edit-loader.js is its
// authoring twin. Both load in order (async = false).
(function () {
  'use strict'
  var self = document.currentScript && document.currentScript.src
  var base = self ? self.replace(/[^/]*$/, '') : 'external/'
  ;['course.js', 'classroom.js'].forEach(function (name) {
    var script = document.createElement('script')
    script.src = base + name
    script.async = false
    document.head.appendChild(script)
  })
})()

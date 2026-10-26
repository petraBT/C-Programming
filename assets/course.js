window.COURSE = {
  name: 'ENGS 20',
  pdfPrefix: 'ENGS20-',
  // Per-course ports, so this book runs beside ENGS 28 (8927/8928/8931) and the demo.
  editPort: 9027,
  reviewPort: 9028,
  // "Follow me": the session client reads the slide number from location.hash.
  scripts: ['classroom.js'],
  // The session server is reached through this site's own /session/ function when deployed. A
  // local preview has no such function, so it uses the deployed site's.
  localSessionOrigin: 'wss://cprog-client-preview.pages.dev',
  // Alt-click a demo slide's coding window (while authoring) to open its starting point here.
  startPoints: 'http://127.0.0.1:5050'
}

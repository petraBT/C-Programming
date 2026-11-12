// Every address under the old host lands here -- the root on index.html, any
// other path on 404.html, which GitHub Pages serves for anything it cannot
// find. Both send the visitor to the SAME path on the book's own hostname, so
// a link saved to one page still opens that page.
//
// This branch used to BE the ENGS 20 book, at petrabt.github.io/C-Programming/.
// That prefix is not part of the new address, so it comes off. The static
// copy, which lived under /C-Programming/static/, keeps its /static/ prefix:
// stripping /C-Programming leaves it in place, which is where it now lives.
(function () {
  var NEW = 'https://engs20book.thayer.dartmouth.edu';
  var path = location.pathname.replace(/^\/C-Programming(?=\/|$)/, '');
  if (path.charAt(0) !== '/') path = '/' + path;
  location.replace(NEW + path + location.search + location.hash);
})();

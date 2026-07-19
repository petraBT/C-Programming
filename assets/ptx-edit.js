// Authoring aid: get from a paragraph in the book back to its PreTeXt source.
//
//   alt-click        a paragraph -> opens that spot in your text editor
//   alt-shift-click  a paragraph -> edit the text right here, then save
//
// Loaded on every page via the html.js.extra stringparam, but ONLY by the
// "web-edit" target (see project.ptx), so it never ships with a deployed book.
// It is also inert on its own: everything below needs scripts/edit-server.py
// listening on localhost, and it does nothing at all until you hold alt.
//
// The server is what knows how to find the source - this file just reports
// which block was clicked and what its text says. See scripts/edit-server.py.
(function () {
  'use strict'

  var SERVER = 'http://127.0.0.1:8927'

  // Blocks PreTeXt gives an id to and that hold prose worth editing. Anything
  // else the click bubbles up from until it reaches one of these.
  var BLOCKS = '.para, li, article, .heading, h1, h2, h3, h4, h5, h6, blockquote, figcaption, td, th'

  var editing = null // the element currently open for in-place editing

  function toast (message, kind) {
    var existing = document.getElementById('ptx-edit-toast')
    if (existing) existing.remove()
    var node = document.createElement('div')
    node.id = 'ptx-edit-toast'
    node.className = 'ptx-edit-toast ptx-edit-toast-' + (kind || 'info')
    node.textContent = message
    document.body.appendChild(node)
    // Errors stay up long enough to actually read; confirmations don't linger.
    setTimeout(function () {
      if (node.parentNode) node.remove()
    }, kind === 'error' ? 6000 : 2500)
  }

  function blockFor (target) {
    if (!target || !target.closest) return null
    var content = target.closest('#ptx-content')
    if (!content) return null // masthead, sidebar, footer - not book text
    var block = target.closest(BLOCKS)
    return block && content.contains(block) ? block : null
  }

  // The block's own id, or the nearest ancestor's - the server uses it to
  // narrow its text search to the right chapter before matching.
  function idFor (block) {
    var node = block
    while (node && node.id === '') node = node.parentElement
    return node && node.id ? node.id : ''
  }

  // PreTeXt puts a "🔗" permalink widget inside every block. It is decoration,
  // not prose, so it has to be excluded before the text is matched against the
  // source - and especially before an in-place edit, or the glyph would be
  // written into the .ptx file. Hiding it (rather than stripping a detached
  // clone) keeps innerText's block-aware spacing, which textContent would lose.
  // Only .autopermalink is hidden: a broader rule such as everything
  // aria-hidden would also swallow MathJax's visual output.
  function withoutChrome (block, read) {
    var hidden = block.querySelectorAll('.autopermalink')
    hidden.forEach(function (node) { node.style.display = 'none' })
    try {
      return read()
    } finally {
      hidden.forEach(function (node) { node.style.removeProperty('display') })
    }
  }

  function textFor (block) {
    return withoutChrome(block, function () {
      return (block.innerText || block.textContent || '').replace(/\s+/g, ' ').trim()
    })
  }

  function openInEditor (block) {
    var url = SERVER + '/locate?open=1' +
      '&text=' + encodeURIComponent(textFor(block)) +
      '&id=' + encodeURIComponent(idFor(block))
    fetch(url)
      .then(function (response) { return response.json().then(function (body) {
        if (!response.ok) throw new Error(body.error || 'lookup failed')
        return body
      }) })
      .then(function (body) { toast('Opened ' + body.file + ':' + body.line, 'ok') })
      .catch(function (error) { toast(describe(error), 'error') })
  }

  function describe (error) {
    // A fetch that never reached anything means the helper isn't running,
    // which is by far the most common thing to go wrong here.
    if (error instanceof TypeError) {
      return 'Edit server not running - start it with: python3 scripts/edit-server.py'
    }
    return error.message
  }

  function beginEdit (block) {
    if (editing) return
    var original = textFor(block)
    editing = block
    // Take the permalink widget out for the duration - inside a contenteditable
    // region it is just something to accidentally delete, and it must not end up
    // in the text we send to the server.
    var permalinks = [].slice.call(block.querySelectorAll('.autopermalink'))
    permalinks.forEach(function (node) { node.remove() })
    // Snapshot the markup, not just the words: abandoning an edit has to put
    // back the inline <code>/<em> rendering too, not flatten it to plain text.
    var originalHTML = block.innerHTML
    block.classList.add('ptx-edit-active')
    block.setAttribute('contenteditable', 'plaintext-only')
    block.focus()

    function revert () {
      block.innerHTML = originalHTML
    }
    function restoreChrome () {
      permalinks.forEach(function (node) { block.appendChild(node) })
    }

    function finish (save) {
      if (editing !== block) return
      editing = null
      block.removeAttribute('contenteditable')
      block.classList.remove('ptx-edit-active')
      block.removeEventListener('keydown', onKey)
      block.removeEventListener('blur', onBlur)

      var updated = textFor(block)
      if (!save || updated === original) {
        revert()
        restoreChrome()
        return
      }
      fetch(SERVER + '/patch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: original, newText: updated, id: idFor(block) })
      })
        .then(function (response) { return response.json().then(function (body) {
          if (!response.ok) throw new Error(body.error || 'save failed')
          return body
        }) })
        .then(function (body) {
          restoreChrome()
          toast('Saved to ' + body.file + ':' + body.line, 'ok')
        })
        .catch(function (error) {
          // The source is the truth; if the write didn't land, don't leave the
          // page showing an edit that only exists in this tab.
          revert()
          restoreChrome()
          toast(describe(error), 'error')
        })
    }

    function onKey (event) {
      if (event.key === 'Escape') {
        event.preventDefault()
        finish(false)
      } else if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
        event.preventDefault()
        finish(true)
      } else if (event.key === 'Enter') {
        event.preventDefault() // one block is one paragraph; no newlines
      }
    }
    function onBlur () { finish(true) }

    block.addEventListener('keydown', onKey)
    block.addEventListener('blur', onBlur)
    toast('Editing - ⌘⏎ to save, esc to cancel', 'info')
  }

  document.addEventListener('click', function (event) {
    if (!event.altKey || editing) return
    var block = blockFor(event.target)
    if (!block) return
    event.preventDefault()
    event.stopPropagation()
    if (event.shiftKey) beginEdit(block)
    else openInEditor(block)
  }, true)

  // Hold alt to see what a click would land on.
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Alt') document.body.classList.add('ptx-edit-armed')
  })
  document.addEventListener('keyup', function (event) {
    if (event.key === 'Alt') document.body.classList.remove('ptx-edit-armed')
  })
  window.addEventListener('blur', function () {
    document.body.classList.remove('ptx-edit-armed')
  })

  var style = document.createElement('style')
  style.textContent = [
    '.ptx-edit-armed #ptx-content :is(' + BLOCKS + '):hover {',
    '  outline: 2px solid #2b8a3e; outline-offset: 3px;',
    '  border-radius: 2px; cursor: pointer;',
    '}',
    '.ptx-edit-active {',
    '  outline: 2px solid #1c7ed6 !important; outline-offset: 3px;',
    '  background: rgba(28,126,214,.06);',
    '}',
    '.ptx-edit-toast {',
    '  position: fixed; bottom: 18px; right: 18px; z-index: 10000;',
    '  max-width: 30em; padding: 10px 14px; border-radius: 6px;',
    '  font: 14px/1.4 system-ui, sans-serif; color: #fff;',
    '  box-shadow: 0 2px 12px rgba(0,0,0,.25);',
    '}',
    '.ptx-edit-toast-ok { background: #2b8a3e; }',
    '.ptx-edit-toast-error { background: #c92a2a; }',
    '.ptx-edit-toast-info { background: #343a40; }'
  ].join('\n')
  document.head.appendChild(style)
})()

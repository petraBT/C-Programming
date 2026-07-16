# CanvasStartDir

Starting points for Canvas short assignments, quizzes, and tests - things
that aren't part of the book itself, so they don't belong in `CMeCodeDir/`
(which is reserved for starting points actually referenced by a
`<cmecode startPoint="...">` in `source/**/*.ptx`).

Organized in one subfolder per category (`Short Assignment/`, `Canvas Quiz/`,
`Test/`, ...) - whatever category names already exist as subfolders here
*are* the category list; there's no separate registry to keep in sync.
Category names are free-form (spaces are fine) and don't need to match any
fixed scheme - use whatever groups these the way you actually think about
them.

Managed via `../starting-points-tool/` (browse, create, edit, and generate
Canvas embed HTML for anything in here or in `CMeCodeDir/`) rather than by
hand - see that tool's own comments for how it's organized. Files placed
here manually work fine too; the tool just lists whatever it finds.

Once committed and deployed (`./deploy-client-preview.sh`), each file here is
reachable at `https://<deployed-site>/CanvasStartDir/<category>/<name>.c`,
the same way `CMeCodeDir/<name>.c` already is for book exercises.

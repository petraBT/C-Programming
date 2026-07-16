# QuizStartDir

Starting points for Canvas quizzes/tests/one-off exercises that aren't part
of the book itself, so they don't belong in `CMeCodeDir/` (which is reserved
for starting points actually referenced by a `<cmecode startPoint="...">` in
`source/**/*.ptx`).

Organized in one subfolder per topic (`arrays/`, `pointers/`, `loops/`, ...) -
whatever topic names already exist as subfolders here *are* the topic list;
there's no separate registry to keep in sync. Topic names are free-form and
don't need to match the book's current chapter titles exactly - use whatever
groups these the way you actually think about them.

Managed via `../starting-points-tool/` (browse, create, and generate Canvas
embed HTML for anything in here or in `CMeCodeDir/`) rather than by hand -
see that tool's own comments for how it's organized. Files placed here
manually work fine too; the tool just lists whatever it finds.

Once committed and deployed (`./deploy-client-preview.sh`), each file here is
reachable at `https://<deployed-site>/QuizStartDir/<topic>/<name>.c`, the
same way `CMeCodeDir/<name>.c` already is for book exercises.

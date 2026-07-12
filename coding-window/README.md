Built output of the client-side C coding-window tool (compiles and runs C
entirely in the browser, no server). Source lives in a separate repo:
https://github.com/petraBT/C-InBroserEnvironment (or wherever that ends up
being hosted — check with whoever built it if this link goes stale).

To update: rebuild there (`npm run build`), then replace the contents of
this directory with that repo's `dist/` output. Don't hand-edit anything
in here directly — it's generated.

See that repo's own README.md and DEPLOYMENT.md for how it works and how
it's wired into this book (the `client` cmecode.mode in
`xsl/c-programming-html.xsl`, and the copy-CMeCodeDir step in `deploy.sh`).

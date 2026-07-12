#!/bin/bash
set -e

# Builds "web" and "web-static" independently, injects the sorting-algorithm applets
# into both, then assembles them onto the gh-pages branch ourselves: "web" lands
# exactly where it always has (site root, existing bookmarks unchanged), and
# "web-static" lands under /static/. We do this assembly by hand with a git worktree
# rather than via `pretext deploy`, since PreTeXt's own deploy-dir/site mechanism
# can't keep one target unchanged at root while adding another as a subfolder (see
# the comment on the web-static target in project.ptx).
#
# Opt-in third target: DEPLOY_CLIENT=1 ./deploy.sh also builds and publishes "web-client"
# (the new client-side coding-window tool, evaluation stage) under /client-preview/,
# alongside "web" and "web-static" without touching either. Off by default so a plain
# ./deploy.sh behaves exactly as it always has.

WORKTREE_DIR=".gh-pages-worktree"

# `pretext deploy -u` used to also commit and push your source changes (the
# --update-source flag) at the same time as deploying. Since we no longer call
# `pretext deploy` at all, do that ourselves here, on whatever branch you currently
# have checked out (normally main), before touching gh-pages at all.
git add -A
if git diff --cached --quiet; then
    echo "No source changes to commit."
else
    git commit -m "Update source ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
fi
git push origin HEAD

pretext build web
pretext build web-static

./scripts/add-applets.sh output/web
./scripts/add-applets.sh output/web-static

if [ "${DEPLOY_CLIENT:-}" = "1" ]; then
    pretext build web-client
fi

# Set up a persistent worktree checked out to gh-pages, so publishing never touches
# your actual working directory or your current branch.
if [ ! -d "$WORKTREE_DIR" ]; then
    git fetch origin gh-pages
    git worktree add "$WORKTREE_DIR" gh-pages
fi

cd "$WORKTREE_DIR"
git fetch origin gh-pages
git checkout gh-pages
git reset --hard origin/gh-pages

# Wipe everything except .git, then repopulate from this build.
find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +

cp -R ../output/web/. .
mkdir -p static
cp -R ../output/web-static/. static/

if [ "${DEPLOY_CLIENT:-}" = "1" ]; then
    # coding-window/ and CMeCodeDir/ need to be siblings of the built pages themselves
    # (not nested inside each other) -- that's what the relative paths the XSL generates
    # (coding-window/index.html?src=../CMeCodeDir/<name>.c) assume. See the cmecode.client.*
    # param comments in xsl/c-programming-html.xsl for why.
    mkdir -p client-preview
    cp -R ../output/web-client/. client-preview/
    cp -R ../coding-window client-preview/
    mkdir -p client-preview/CMeCodeDir
    find ../CMeCodeDir -maxdepth 1 -name '*.c' -exec cp {} client-preview/CMeCodeDir/ \;
fi

# GitHub Pages runs Jekyll by default, which ignores underscore-prefixed folders
# like PreTeXt's _static/ -- this file tells it not to.
touch .nojekyll

git add -A
if git diff --cached --quiet; then
    echo "Nothing changed since the last deploy -- skipping commit/push."
else
    git commit -m "Deploy update ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
    git push origin gh-pages
fi
cd - > /dev/null

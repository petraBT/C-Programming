#!/bin/bash

# Builds both versions of the book: "web" (live, Thayer-network-dependent code
# windows) and "web-static" (offline-friendly, copy-pasteable code windows).
# See the "Building and deploying" section of README.md for why there are two.
pretext build web
./scripts/add-applets.sh output/web

pretext build web-static
./scripts/add-applets.sh output/web-static

# bash -c "sleep 2; open http://localhost:8000/" &
pretext view web

# gitpush
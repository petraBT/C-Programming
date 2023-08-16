#!/bin/bash

pretext build web
./AddApplets.sh
# bash -c "sleep 2; open http://localhost:8000/" & 
pretext view web

# gitpush
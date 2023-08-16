#!/bin/bash

#cd output/html/
#cd ../ENGS20/c-programming/
cd output/web/
for file in `ls -1 sort*.html`; do 
	python3 findapplets.py $file; 
done 

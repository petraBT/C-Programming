#!/bin/bash
for file in `grep "code into the code submission box" -r --include="*.ptx" | awk -F ':' '{print $1}'`; \
	#cat $file | sed -n '/student code starts here/,/student code ends here/p' | tail -n +2 > tmp.c; \
	cat $file | sed -n '/code submission box/,/interactive="yes"/p'
done

for file in `grep "keyword" -r --include="*.ptx" | awk -F ':' '{print $1}'`
    sed -i'.old' 's/be given a keyword to enter below. Please enter the keyword exactly as given to you (without the quotation marks)./be given a keyword to enter in Canvas./g' $file

grep "Enter your choice" -r --include="*.ptx"


#get those xml:id's: 
#grep "<program xml:id=" -r --include="*.ptx" | awk '{print $3}'

#get activities without xml ids:
#cat array.ptx | sed -n '/<activity>/,/activity>/p'

#######
#cd ../CMeCodeDir; \
#for file in *.c; do \
#	echo "<?xml version='1.0'?>" > $file.xml; \
#	echo '<cme>' >> $file.xml; \
#	sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' $file >> $file.xml; \
#	echo '</cme>' >> $file.xml; \
#done

#cd ../CodecastDir; \
#for file in *.c; do \
#	echo "<?xml version='1.0'?>" > $file.xml; \
#	echo '<cme>' >> $file.xml; \
#	sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' $file >> $file.xml; \
#	echo '</cme>' >> $file.xml; \
#done

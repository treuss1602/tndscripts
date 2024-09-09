#!/bin/bash

file1=$1
file2=$2

xmllint --format $file1 | sed -e's# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" # #' >a.xml
xmllint --format $file2 | sed -e's# xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" # #' >b.xml
(echo "< $file1"; echo "> $file2"; diff a.xml b.xml) | less
rm a.xml b.xml

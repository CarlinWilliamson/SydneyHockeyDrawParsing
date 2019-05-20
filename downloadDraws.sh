#!/bin/sh

for i in `wget https://www.sydneyhockey.com.au/games/ -O- -q | grep L | grep a\> | tr -d " "`
do
	name=`echo $i | cut -d'"' -f7 | sed -E "s/.*([A-Z]{2}[0-9]).*/\1/g"`.pdf
	wget `echo $i | cut -d'"' -f4 | sed -E "s|games/|reports/games/download/\&c=|" | sed -E "s|/\&amp;|\&|g"` -O $name -q
	echo downloaded $name
done




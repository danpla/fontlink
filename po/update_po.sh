#!/bin/sh

rm -f fontlink.desktop.in.h
rm -f fontlink.desktop.in
cp ../data/fontlink.desktop fontlink.desktop.in
sed -e '/Comment\[/ d' \
    -e 's/Comment/_Comment/' \
    -i fontlink.desktop.in
intltool-extract --quiet --type=gettext/ini fontlink.desktop.in


xgettext --files-from=POTFILES.in --from-code=UTF-8  \
    -D.. -D. --output=fontlink.pot --keyword=N_ fontlink.desktop.in.h

for i in *.po;
do
    echo $i
    msgmerge -q --update --no-fuzzy-matching --backup=off $i fontlink.pot;
done


intltool-merge --quiet --desktop-style \
    . fontlink.desktop.in ../data/fontlink.desktop
rm -f fontlink.desktop.in.h
rm -f fontlink.desktop.in

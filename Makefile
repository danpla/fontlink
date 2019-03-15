
.PHONY: all
all: build

.PHONY: build
build:
	python3 -m compileall fontlink
	for l in `grep -v '^#' po/LINGUAS`; \
	do \
		modir=mo/$$l/LC_MESSAGES; \
		mkdir -p $$modir; \
		msgfmt po/$$l.po --output-file $$modir/fontlink.mo; \
	done

.PHONY: clean
clean:
	find fontlink -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf mo

.PHONY: install
install:
	install bin/fontlink /usr/bin
	cp -r fontlink /usr/share

	cp -r mo/* /usr/share/locale

	cp -r data/icons/hicolor /usr/share/icons
	gtk-update-icon-cache -q -t /usr/share/icons/hicolor

	cp data/fontlink.desktop /usr/share/applications

.PHONY: uninstall
uninstall:
	rm -f /usr/bin/fontlink
	rm -rf /usr/share/fontlink

	for l in `grep -v '^#' po/LINGUAS`; \
	do \
		rm -f /usr/share/locale/$$l/LC_MESSAGES/fontlink.mo; \
	done

	for i in data/icons/hicolor/*; \
	do \
		rm -f /usr/share/icons/hicolor/`basename $$i`/apps/fontlink.*; \
	done
	gtk-update-icon-cache -q -t /usr/share/icons/hicolor

	rm -f /usr/share/applications/fontlink.desktop

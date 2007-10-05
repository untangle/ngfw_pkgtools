DISTRIBUTION ?= $(USER)
TARGET_DISTRIBUTION ?= sarge
PACKAGE_SERVER = mephisto
BUILDTOOLS_DIR = $(shell dirname $(MAKEFILE_LIST))

checkroot:
	@if [ "$$UID" = "0" ]; then \
	  echo "You can't be root to build packages"; \
	  exit 1; \
	fi

clean: checkroot
	svn revert debian/changelog
	fakeroot debian/rules clean
	rm -f debian/version

version: checkroot
	svn revert debian/changelog
	sh $(BUILDTOOLS_DIR)/incVersion.sh $(DISTRIBUTION) $(VERSION)

source: checkroot
	# so we can use that later to find out what to upload if needs be
	dpkg-parsechangelog | awk '/Version: / { gsub(/^.+:/, "", $$2) ; print $$2 }' >| debian/version
	tar cz --exclude="*stamp*" \
		--exclude=".svn" \
		--exclude="debian" \
		--exclude="todo" \
		--exclude="staging" \
		--exclude="dist" \
		-f ../`dpkg-parsechangelog | awk '/Source: / { print $$2 }'`_`perl -npe 's/(.+)-.*/$$1/' debian/version`.orig.tar.gz ../`basename $$(pwd)`

# FIXME: duplicate code between pkg and pkg-pbuilder
pkg: checkroot
	# so we can use that later to find out what to upload if needs be
	dpkg-parsechangelog | awk '/Version: / { print $$2 }' >| debian/version
	# FIXME: sign packages when we move to apt 0.6
	# FIXME: don't clean before building !!!
	/usr/bin/debuild -e HADES_KEYSTORE -e HADES_KEY_ALIAS -e HADES_KEY_PASS -i -us -uc
	svn revert debian/changelog

pkg-chroot: checkroot
	# so we can use that later to find out what to upload if needs be
	dpkg-parsechangelog | awk '/Version: / { print $$2 }' >| debian/version
	# FIXME: sign packages when we move to apt 0.6
	# FIXME: don't clean before building !!!
	# FIXME: do we need to preserve HADES_* in this case ?
	pdebuild --pbuilder cowbuilder --use-pdebuild-internal --debbuildopts "-i -us -uc" -- --basepath /var/cache/pbuilder/$(TARGET_DISTRIBUTION).cow
	svn revert debian/changelog

release: checkroot
	dput -c $(BUILDTOOLS_DIR)/dput.cf $(PACKAGE_SERVER) ../`dpkg-parsechangelog | awk '/Source: / { print $$2 }'`_`cat debian/version`*.changes

.PHONY: checkroot clean version source pkg release

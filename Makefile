DISTRIBUTION ?= $(USER)
SHELL = /bin/bash
shell = /bin/bash
PACKAGE_SERVER = mephisto
PACKAGE_NAME = $(shell basename `pwd`)
BUILDTOOLS_DIR = $(shell dirname $(MAKEFILE_LIST))
CHROOT_DIR = /var/cache/pbuilder
CHROOT_UPDATE_SCRIPT = $(BUILDTOOLS_DIR)/chroot-update.sh
CHROOT_CHECK_PACKAGE_VERSION_SCRIPT = $(BUILDTOOLS_DIR)/chroot-check-for-package-version.sh
AVAILABILITY_MARKER = __NOT-AVAILABLE__

.PHONY: checkroot clean version check-existence source pkg pkg-chroot release release-deb

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
	bash $(BUILDTOOLS_DIR)/incVersion.sh $(DISTRIBUTION) VERSION=$(VERSION) REPOSITORY=$(REPOSITORY)
	dpkg-parsechangelog | awk '/Version: / { print $$2 }' >| debian/version

check-existence: checkroot
	CHROOT_ORIG=$(CHROOT_DIR)/$(REPOSITORY)+untangle.cow ; \
	CHROOT_WORK=$(CHROOT_DIR)/$(REPOSITORY)+untangle_`date "+%Y-%m-%dT%H%M%S_%N"`.cow ; \
	sudo cp -al $${CHROOT_ORIG} $${CHROOT_WORK} ; \
        sudo cowbuilder --execute --basepath $${CHROOT_WORK} --save-after-exec -- $(CHROOT_UPDATE_SCRIPT) $(REPOSITORY) $(DISTRIBUTION) ; \
	output=`sudo cowbuilder --execute --basepath $${CHROOT_WORK} -- $(CHROOT_CHECK_PACKAGE_VERSION_SCRIPT) $(shell awk '/^Package: / {print $$2 ; exit}' debian/control) $(shell cat debian/version) $(AVAILABILITY_MARKER)` ; \
	sudo rm -fr $${CHROOT_WORK} ; \
	echo "$${output}" | grep -q $(AVAILABILITY_MARKER) && echo "Version $(shell cat debian/version) of $(PACKAGE_NAME) is not available in $(REPOSITORY) $(DISTRIBUTION)"

source: checkroot
	# so we can use that later to find out what to upload if needs be
	dpkg-parsechangelog | awk '/Version: / { print $$2 }' >| debian/version
	tar cz --exclude="*stamp*" \
		--exclude=".svn" \
		--exclude="debian" \
		--exclude="todo" \
		--exclude="staging" \
		-f ../`dpkg-parsechangelog | awk '/Source: / { print $$2 }'`_`perl -npe 's/(.+)-.*/$$1/ ; s/^.+://' debian/version`.orig.tar.gz ../`basename $$(pwd)`

# FIXME: duplicate code between pkg and pkg-chroot
pkg: checkroot
	# so we can use that later to find out what to upload if needs be
	dpkg-parsechangelog | awk '/Version: / { print $$2 }' >| debian/version
	# FIXME: sign packages when we move to apt 0.6
	/usr/bin/debuild -e HADES_KEYSTORE -e HADES_KEY_ALIAS -e HADES_KEY_PASS -i -us -uc -sa
	svn revert debian/changelog

pkg-chroot: checkroot
	# so we can use that later to find out what to upload if needs be
	dpkg-parsechangelog | awk '/Version: / { print $$2 }' >| debian/version
	# FIXME: sign packages themselves ?
	export HADES_KEY_PASS=Boo4fiuzaiph7ah ; \
	export HADES_KEY_ALIAS=key ; \
	CHROOT_ORIG=$(CHROOT_DIR)/$(REPOSITORY)+untangle.cow ; \
	CHROOT_WORK=$(CHROOT_DIR)/$(REPOSITORY)+untangle_`date "+%Y-%m-%dT%H%M%S_%N"`.cow ; \
	sudo rm -fr $${CHROOT_WORK} ; \
	sudo cp -al $${CHROOT_ORIG} $${CHROOT_WORK} ; \
        sudo cowbuilder --execute --basepath $${CHROOT_WORK} --save-after-exec -- $(CHROOT_UPDATE_SCRIPT) $(REPOSITORY) $(DISTRIBUTION) ; \
	pdebuild --pbuilder cowbuilder --use-pdebuild-internal \
				 --buildresult .. --debbuildopts "-i -us -uc -sa" -- --basepath $${CHROOT_WORK} --debug ; \
	sudo rm -fr $${CHROOT_WORK}
	svn revert debian/changelog

release: checkroot
	dput -c $(BUILDTOOLS_DIR)/dput.cf $(PACKAGE_SERVER) ../`dpkg-parsechangelog | awk '/Source: / { print $$2 }'`_`perl -npe 's/^.+://' debian/version`*.changes

release-deb: checkroot
	for p in `find . -name "*.deb"` ; do \
	  touch $${p/.deb/.$(REPOSITORY)_$(DISTRIBUTION).manifest} ; \
	done
	lftp -e "set net:max-retries 1 ; cd incoming ; put `find . -name "*.deb" -o -name "*.manifest" | xargs` ; exit" mephisto
	find . -name "*manifest" | xargs rm -f

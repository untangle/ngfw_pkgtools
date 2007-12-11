DISTRIBUTION ?= $(USER)
SHELL = /bin/bash
shell = /bin/bash
PACKAGE_SERVER = mephisto
PACKAGE_NAME = $(shell basename `pwd`)
BUILDTOOLS_DIR = $(shell dirname $(MAKEFILE_LIST))
CHROOT_DIR = /var/cache/pbuilder
CHROOT_UPDATE_SCRIPT = $(BUILDTOOLS_DIR)/chroot-update.sh

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

check-existence:
	CHROOT_ORIG=$(CHROOT_DIR)/$(REPOSITORY)+untangle.cow ; \
	CHROOT_WORK=$(CHROOT_DIR)/$(REPOSITORY)+untangle_`date "+%Y-%m-%dT%H%M%S_%N"`.cow ; \
	sudo cp -al $${CHROOT_ORIG} $${CHROOT_WORK} ; \
        sudo cowbuilder --execute --basepath $${CHROOT_WORK} --save-after-exec -- $(CHROOT_UPDATE_SCRIPT) $(REPOSITORY) $(DISTRIBUTION) ; \
	sudo cowbuilder --execute \
		        --basepath $${CHROOT_WORK} \
		        -- /bin/bash -c "apt-get update -q ; apt-cache show $(PACKAGE_NAME) | awk '/Version: $(shell cat debian/version)/ {exit 123}'" || [ $$? = 123 ] && echo "Version $(shell cat debian/version) of $(PACKAGE_NAME) is already available in $(REPOSITORY) $(DISTRIBUTION)" && exit 2

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
	CHROOT_ORIG=$(CHROOT_DIR)/$(REPOSITORY)+untangle.cow ; \
	CHROOT_WORK=$(CHROOT_DIR)/$(REPOSITORY)+untangle_`date "+%Y-%m-%dT%H%M%S_%N"`.cow ; \
	sudo cp -al $${CHROOT_ORIG} $${CHROOT_WORK} ; \
        sudo cowbuilder --execute --basepath $${CHROOT_WORK} --save-after-exec -- $(CHROOT_UPDATE_SCRIPT) $(REPOSITORY) $(DISTRIBUTION) ; \
	pdebuild --pbuilder cowbuilder --use-pdebuild-internal \
		 --buildresult .. --debbuildopts "-i -us -uc -sa" -- --basepath $${CHROOT_WORK} ; \
	sudo rm -fr $${CHROOT_WORK}
	svn revert debian/changelog

release: checkroot
	dput -c $(BUILDTOOLS_DIR)/dput.cf $(PACKAGE_SERVER) ../`dpkg-parsechangelog | awk '/Source: / { print $$2 }'`_`perl -npe 's/^.+://' debian/version`*.changes

release-deb: checkroot
	for p in *.deb ; do \
	  touch $${p/.deb/.$(REPOSITORY)_$(DISTRIBUTION).manifest} ; \
	done
	lftp -e "set net:max-retries 1 ; cd incoming ; put `ls ./*.deb ./*manifest | xargs` ; exit" mephisto
	rm -f *manifest

.PHONY: checkroot clean version source pkg release

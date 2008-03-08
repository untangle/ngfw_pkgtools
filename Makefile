# overridables
DISTRIBUTION ?= $(USER)
PACKAGE_SERVER ?= mephisto

# pwd of this Makefile
PKGTOOLS_DIR := $(shell dirname $(MAKEFILE_LIST))

# default shell
SHELL := /bin/bash
shell := /bin/bash

# debuild/dpkg-buildpackage options
DEBUILD_OPTIONS := -e HADES_KEYSTORE -e HADES_KEY_ALIAS -e HADES_KEY_PASS
DPKGBUILDPACKAGE_OPTIONS := -i -us -uc
ifeq ($(origin BINARY_UPLOAD), undefined)
  DPKGBUILDPACKAGE_OPTIONS += -sa
else
  DPKGBUILDPACKAGE_OPTIONS += -b
endif

ifneq ($(origin RECURSIVE), undefined)
  REC := -a
endif

# cwd
CUR_DIR := $(shell basename `pwd`)

# destination dir for the debian files (dsc, changes, etc)
DEST_DIR := /tmp

# current package to build
SOURCE_NAME := $(shell dpkg-parsechangelog | awk '/^Source:/{print $$2}')
VERSION_FILE := debian/version

# chroot stuff
CHROOT_DIR := /var/cache/pbuilder
CHROOT_UPDATE_SCRIPT := $(PKGTOOLS_DIR)/chroot-update.sh
CHROOT_CHECK_PACKAGE_VERSION_SCRIPT := $(PKGTOOLS_DIR)/chroot-check-for-package-version.sh
CHROOT_ORIG := $(CHROOT_DIR)/$(REPOSITORY)+untangle.cow
CHROOT_WORK := $(CHROOT_DIR)/$(REPOSITORY)+untangle_$(shell date "+%Y-%m-%dT%H%M%S_%N").cow

# used for checking existence of a package on the package server
AVAILABILITY_MARKER := __NOT-AVAILABLE__

########################################################################
# Rules
.PHONY: checkroot revert-changelog parse-changelog move-debian-files clean-debian-files clean-build clean version-real version check-existence source pkg-real pkg pkg-chroot-real pkg-chroot release release-deb

checkroot:
	@if [ "$$UID" = "0" ] ; then \
	  echo "You can't be root to build packages"; \
	  exit 1; \
	fi

revert-changelog: # do not leave it locally modified
	svn revert debian/changelog

parse-changelog: # store version so we can use that later for uploading
	dpkg-parsechangelog | awk '/Version:/{print $$2}' >| $(VERSION_FILE)

move-debian-files:
	find .. -maxdepth 1 -name "*`perl -pe 's/^.+://' $(VERSION_FILE)`*" -regex '.*\.\(upload\|changes\|deb\|upload\|dsc\|build\|diff\.gz\)' -exec mv "{}" $(DEST_DIR) \;
	find .. -maxdepth 1 -name "*`perl -pe 's/^.+:// ; s/-.*//' $(VERSION_FILE)`*orig.tar.gz" -exec mv "{}" $(DEST_DIR) \;

clean-build: checkroot revert-changelog
	fakeroot debian/rules clean
	rm -f $(VERSION_FILE)
clean-debian-files: 
	find $(DEST_DIR) -maxdepth 1 -name "*`perl -pe 's/^.+://' $(VERSION_FILE)`*" -regex '.*\.\(changes\|deb\|upload\|dsc\|build\|diff\.gz\)' -exec rm -f "{}" \;
	find $(DEST_DIR) -maxdepth 1 -name "*`perl -pe 's/^.+:// ; s/-.*//' $(VERSION_FILE)`*orig.tar.gz" -exec rm -f "{}" \;
clean: clean-debian-files clean-build

version-real: checkroot
	bash $(PKGTOOLS_DIR)/incVersion.sh $(DISTRIBUTION) VERSION=$(VERSION) REPOSITORY=$(REPOSITORY)
version: version-real parse-changelog

check-existence: checkroot
	sudo cp -al $(CHROOT_ORIG) $(CHROOT_WORK)
	sudo cowbuilder --execute --basepath $(CHROOT_WORK) --save-after-exec -- $(CHROOT_UPDATE_SCRIPT) $(REPOSITORY) $(DISTRIBUTION)
	output=`sudo cowbuilder --execute --basepath $(CHROOT_WORK) -- $(CHROOT_CHECK_PACKAGE_VERSION_SCRIPT) $(SOURCE_NAME) $(shell cat $(VERSION_FILE)) $(AVAILABILITY_MARKER)` ; \
	sudo rm -fr $(CHROOT_WORK) ; \
	echo "$${output}" | grep -q $(AVAILABILITY_MARKER) && echo "Version $(shell cat $(VERSION_FILE)) of $(SOURCE_NAME) is not available in $(REPOSITORY)/$(DISTRIBUTION)"

source: checkroot parse-changelog
	tar cz --exclude="*stamp*" --exclude=".svn" --exclude="debian" \
	       --exclude="todo" --exclude="staging" \
	       -f ../$(SOURCE_NAME)_`dpkg-parsechangelog | awk '/^Version:/{gsub(/(^.+:|-.*)/, "", $$2) ; print $$2}'`.orig.tar.gz ../$(CUR_DIR)

pkg-real: checkroot parse-changelog
	# FIXME: sign packages themselves when we move to apt 0.6
	/usr/bin/debuild $(DEBUILD_OPTIONS) $(DPKGBUILDPACKAGE_OPTIONS)
pkg: pkg-real move-debian-files revert-changelog

pkg-chroot-real: checkroot parse-changelog
	# FIXME: sign packages themselves when we move to apt 0.6
	sudo rm -fr $(CHROOT_WORK)
	sudo cp -al $(CHROOT_ORIG) $(CHROOT_WORK)
	sudo cowbuilder --execute --basepath $(CHROOT_WORK) --save-after-exec -- $(CHROOT_UPDATE_SCRIPT) $(REPOSITORY) $(DISTRIBUTION)
	pdebuild --pbuilder cowbuilder --use-pdebuild-internal \
	         --buildresult $(DEST_DIR) \
	         --debbuildopts "$(DPKGBUILDPACKAGE_OPTIONS)" -- \
	         --basepath $(CHROOT_WORK)
	sudo rm -fr $(CHROOT_WORK)
pkg-chroot: pkg-chroot-real move-debian-files revert-changelog

release: checkroot
	dput -c $(PKGTOOLS_DIR)/dput.cf $(PACKAGE_SERVER) $(DEST_DIR)/$(SOURCE_NAME)_`perl -pe 's/^.+://' $(VERSION_FILE)`*.changes

release-deb: checkroot
	$(PKGTOOLS_DIR)/release-binary-packages.sh -r $(REPOSITORY) -d $(DISTRIBUTION) $(REC)

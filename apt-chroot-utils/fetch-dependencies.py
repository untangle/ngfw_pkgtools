#! /usr/bin/python

import apt, apt_pkg, os.path, re, sys, urllib
import optparse

from lib import aptchroot

TMP_DIR    = '/tmp/foo'

# functions
def parseCommandLineArgs(args):
  usage = "usage: %prog [options] <package> [<package>,...]"

  parser = optparse.OptionParser(usage=usage)
  parser.add_option("-f", "--force-download", dest="forceDownload",
                    action="store_true", default=False,
                    help="Force download of all dependencies" )
  parser.add_option("-d", "--distribution", dest="distribution",
                    action="store", default="nightly",
                    help="Set target distribution" )
  parser.add_option("-i", "--include-only-regex", dest="regex",
                    action="store", default=".",
                    help="Set include regex." )
  parser.add_option("", "--host", dest="host",
                    action="store", default="10.0.0.105",
                    help="Set Untangle mirror host" )  
  parser.add_option("-r", "--repository", dest="repository",
                    action="store", default="lenny",
                    help="Set target repository" )
  parser.add_option("-l", "--local-packages", dest="localPackages",
                    action="store", default="",
                    help="Set target repository" )
  parser.add_option("-s", "--simulate", dest="simulate",
                    action="store_true", default=False,
                    help="Simulate, but do not download" )
  parser.add_option("-u", "--use-debian-mirros", dest="useDebianMirrors",
                    action="store_true", default=False,
                    help="Use Debian mirrors" )
  parser.add_option("-v", "--verbose", dest="verbose",
                    action="store_true", default=False,
                    help="Verbose" )
  parser.add_option("-b", "--backports-and-volatile", dest="backportsAndVolatile",
                    action="store_true", default=False,
                    help="Use backports and volatile repositories" )
  parser.add_option("-m", "--mode", dest="mode",
                    action="store", default="download-dependencies",
                    help="Set mode: 'download-dependencies'(default), 'update-all'" )
  
  options, pkgs = parser.parse_args(args)

  if options.localPackages == "":
    options.localPackages = os.path.join(sys.path[0], '../../upstream_pkgs_%s' % (options.repository))

  if len(args) == 0 and options.mode == 'download-dependencies':
    parser.error("Wrong number of arguments")
    
  return pkgs, options

# main
pkgs, options = parseCommandLineArgs(sys.argv[1:])
sources = '''deb http://%s/public/%s %s main premium upstream\n''' % (options.host,
                                                                      options.repository,
                                                                      options.distribution)

if options.useDebianMirrors:
  sources += '''
# backports
deb http://www.backports.org/debian %s-backports main contrib non-free
# volatile
deb http://volatile.debian.org/debian-volatile %s/volatile main contrib non-free
# main
deb http://ftp.debian.org/debian %s main contrib non-free main/debian-installer
deb http://debian:8080/security %s/updates main contrib non-free''' % (options.repository,
                                                                       options.repository,
                                                                       options.repository,
                                                                       options.repository )

if options.backportsAndVolatile and options.mode == 'download-dependencies':
  volatilePin = 1001
  backportsPin = 1001
else:
  volatilePin = -1001
  backportsPin = -1001

# FIXME? provide a command line way to specify pinning
preferences = '''Package: *
Pin: release l=Untangle
Pin-Priority: 900

Package: *
Pin: release a=stable, o=volatile.debian.org
Pin-Priority: %s

Package: *
Pin: release a=%s-backports
Pin-Priority: %s

Package: *
Pin: release o=Debian
Pin-Priority: 901\n''' % (volatilePin,
                          options.repository,
                          backportsPin) # options.distribution)

aptchroot.initializeChroot(TMP_DIR, sources, preferences)

lp = aptchroot.LocalPackages(options.localPackages)

if options.mode == 'download-dependencies':
  for arg in pkgs:
    pkg = aptchroot.VersionedPackage(arg)

    deps = pkg.getAllDeps()

    for p in deps:
      try:
        versionedPackage = aptchroot.VersionedPackage(p.name)
        if options.verbose:
          print "*** ", versionedPackage.name, versionedPackage.version

        if versionedPackage.isVirtual:
          if options.verbose:
            print "%s won't be downloaded since it is virtual." % p.name
          continue
        elif (versionedPackage.isRequired or versionedPackage.isImportant or versionedPackage.isStandard) and not options.forceDownload:
          if options.verbose:
            print "%s won't be downloaded since --force-download wasn't used." % p.name
          continue

        if not lp.has(versionedPackage):
          if options.simulate:
            if re.search(options.regex, p.name):
              print "%s" % p.name
          else:
            print "Package %s is missing" % p.name
        elif lp.has(versionedPackage):
          if not lp.get(versionedPackage).satisfies(p):
            if options.verbose:
              print "Version of %s doesn't satisfy dependency (%s)" % (versionedPackage.name, p)
              print "Downloading new one, but you probably want to remove the older one (%s)" % lp.getByName(p.name)
          elif lp.get(versionedPackage).version < versionedPackage.version:
            if options.verbose:
              print "New version of %s available (%s)" % (versionedPackage.name, versionedPackage.version)
              print "Downloading new one, but you probably want to remove the older one (%s)" % lp.getByName(p.name)
          else:
            if options.verbose:
              print "Download of %s (version %s) explicitely requested, but we already have that package" % (versionedPackage.name, versionedPackage.version)
            continue
        else:
          continue

        if not options.simulate:
          versionedPackage.download()
          lp.add(versionedPackage)

      except Exception,e:
        print p, type(p), p.name, dir(p)
        raise
  #      sys.exit(1)
    #  else:
    #    print "%s is in the store and satisfies the dependency" % lp.get(versionedPackage)
elif options.mode == 'update-all':
   for pkg in lp.getPkgs():
    newPkg = aptchroot.VersionedPackage(pkg.name)
    if options.verbose:
      print "%s: local=%s remote=%s" % (pkg.name, pkg.version, newPkg.version)
    if newPkg.version and not pkg.version.find('bpo') > 0 and not pkg.version.find('volatile') > 0 and apt_pkg.VersionCompare(pkg.version, newPkg.version) < 0:
      pkgPath = pkg.fileName
      newName = os.path.basename(newPkg.fileNameWithEpoch)
      newPath = os.path.join(os.path.dirname(pkgPath), newName)
      print "%s: %s -> %s" % (newPkg.name, pkg.version, newPkg.version)
      os.system("svn rm %s" % (pkgPath,))
      newPkg.download()
      lp.add(newPkg)
      os.system("mv %s %s 2> /dev/null" % (newName, newPath))
      os.system("svn add %s" % (newPath))

#os.system('rm -fr ' + TMP_DIR)

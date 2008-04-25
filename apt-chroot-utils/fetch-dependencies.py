#! /usr/bin/python

import apt, apt_pkg, os.path, re, sys, urllib
import optparse

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "lib"))
import aptchroot

TMP_DIR    = '/tmp/foo'

# functions
def parseCommandLineArgs(args):
  usage = "usage: %prog [options] <package> [<package>,...]"

  parser = optparse.OptionParser(usage=usage)
  parser.add_option("-f", "--force-download", dest="forceDownload",
                    action="store_true", default=False,
                    help="Force download of all dependencies" )
  parser.add_option("-d", "--distribution", dest="distribution",
                    action="store", default="sarge",
                    help="Set target distribution" )
  
  options, args = parser.parse_args(args)
  
  if len(args) == 0:
    parser.error("Wrong number of arguments")
  else:
    pkgs = args
    
  return pkgs, options



class UntangleStore:
  reObj = re.compile(r'([^_]+)_([^_]+)_[^\.]+\.deb')

  def __init__(self, basedir):
    self.basedir = basedir
    self.pkgs = {}
    for root, dirs, files in os.walk(basedir):
      if root.count('/.svn'):
        continue
      for f in files:
        m = UntangleStore.reObj.match(f)
        if m:
#          print "Found in store: %s (%s)" % (m.group(1), m.group(2))
          self.pkgs[m.group(1)] = aptchroot.VersionedPackage(m.group(1),
                                                             m.group(2),
                                                             os.path.join(root, f))

  def add(self, pkg):
    self.pkgs[pkg.name] = pkg

  def has(self, pkg):
    return pkg.name in self.pkgs

  def getByName(self, name):
    return self.pkgs[name]

  def get(self, pkg):
    return self.pkgs[pkg.name]

  def __str__(self):
    s = ""
    for p in self.pkgs.values():
      s += "%s\n" % p
    return s[:-1]

# main

pkgs, options = parseCommandLineArgs(sys.argv[1:])
sources = '''deb http://http.us.debian.org/debian %s main contrib non-free
deb http://security.debian.org/ %s/updates main contrib non-free
#php5
#deb http://people.debian.org/~dexter php5 woody
# backports
deb http://www.backports.org/debian %s-backports main contrib non-free
# volatile
deb http://volatile.debian.org/debian-volatile %s/volatile main contrib non-free
# mephisto
deb http://10.0.0.105/public/%s stable main premium upstream\n''' % (options.distribution,
                                                                     options.distribution,
                                                                     options.distribution,
                                                                     options.distribution,
                                                                     options.distribution)
preferences = '''Package: *
Pin: release l=Untangle
Pin-Priority: 1001
Package: *
Pin: origin volatile.debian.org
Pin-Priority: 1001
Package: *
Pin: origin www.backports.org
Pin-Priority: 1001
Package: *
Pin: release o=Debian
Pin-Priority: 100\n''' # % (options.distribution,) # options.distribution)

aptchroot.initializeChroot(TMP_DIR, sources, preferences)

us = UntangleStore(os.path.join(sys.path[0], '../../upstream_pkgs_%s' % (options.distribution)))

for arg in pkgs:
  pkg = aptchroot.VersionedPackage(arg)

  deps = pkg.getAllDeps()
  
  for p in deps:
    try:
      versionedPackage = aptchroot.VersionedPackage(p.name)
#      print "*** ", versionedPackage.name, versionedPackage.version

      if (versionedPackage.isVirtual or versionedPackage.isRequired or versionedPackage.isImportant or versionedPackage.isStandard) and not options.forceDownload:
        print "%s won't be downloaded since --force-download wasn't used." % p.name
        continue

      if not us.has(versionedPackage):
        print "Package %s is missing" % p.name
      elif us.has(versionedPackage):
        if versionedPackage.name in pkgs:
          print "Download explicitely requested"
        elif not us.get(versionedPackage).satisfies(p):
          print "Version of %s doesn't satisfy dependency (%s)" % (us.get(versionedPackage), p)
          print "Downloading new one, but you probably want to remove the older one (%s)" % us.getByName(p.name)
        else:
          continue
      else:
        continue
      
      versionedPackage.download()
      us.add(versionedPackage)

    except Exception,e:
      print p, type(p), p.name, dir(p)
      raise
#      sys.exit(1)
  #  else:
  #    print "%s is in the store and satisfies the dependency" % us.get(versionedPackage)

os.system('rm -fr ' + TMP_DIR)

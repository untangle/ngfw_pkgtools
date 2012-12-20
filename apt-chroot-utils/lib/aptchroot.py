import commands, os, os.path, re, sys, urllib

MINIMUM_VERSION = '0.7.7.1'

MSG = "You need to install python-apt >= %s" % (MINIMUM_VERSION,)

def error():
  print MSG
  sys.exit(1)

try:
  import apt, apt_pkg
except:
  error()

# for i, j in zip(map(int, apt.apt_pkg.Version.split('.')),
#                 map(int, MINIMUM_VERSION.split('.'))):
#   if i < j:
#     error()
#   if i > j:
#     break

# constants
ARCHITECTURE = commands.getoutput('dpkg-architecture -qDEB_BUILD_ARCH')

ops = { '<=' : lambda x: x <= 0,
        '<'  : lambda x: x < 0,
        '=' :  lambda x: x == 0,
        '>'  : lambda x: x > 0,
        '>=' : lambda x: x >= 0 }

def initializeChroot(TMP_DIR, sources, preferences):
  # FIXME
  global cache, pkgCache, depcache

  APT_DIR    = TMP_DIR + '/etc/apt'
  SOURCES    = APT_DIR + '/sources.list'
  PREFS      = APT_DIR + '/preferences'
  CACHE_DIR  = TMP_DIR + '/var/cache/apt'
  ARCHIVES   = CACHE_DIR + '/archives'
  STATE      = TMP_DIR + '/var/lib/apt'
  LISTS      = STATE + '/lists'
  STATUS_DIR = TMP_DIR + '/var/lib/dpkg'
  STATUS     = STATUS_DIR + '/status'
  
  os.system('rm -fr ' + TMP_DIR)
  os.makedirs(APT_DIR)
  os.makedirs(ARCHIVES + '/partial')
  os.makedirs(STATE)
  os.makedirs(LISTS + '/partial')
  os.makedirs(STATUS_DIR)

  # touch status file
  open(STATUS, 'w')
  
  # create sources.list file
  open(SOURCES, 'w').write(sources)
  
  # create preferences files
  open(PREFS, 'w').write(preferences)

  apt_pkg.init()

  apt_pkg.Config.set("Dir", TMP_DIR)
  apt_pkg.Config.set("Dir::Etc", "etc/apt/")
  apt_pkg.Config.set("Dir::Etc::sourcelist", os.path.basename(SOURCES))
  apt_pkg.Config.set("Dir::Etc::preferences", os.path.basename(PREFS))
  apt_pkg.Config.set("Dir::Cache", "var/cache/apt")
  apt_pkg.Config.set("Dir::Cache::Archives", os.path.basename(ARCHIVES))
  apt_pkg.Config.set("Dir::State", "var/lib/apt/")
  apt_pkg.Config.set("Dir::State::Lists",  "lists/")
  apt_pkg.Config.set("Dir::State::status", STATUS)

#   apt_pkg.Config.Set("Debug::pkgPolicy","1");
#   apt_pkg.Config.Set("Debug::pkgOrderList","1");
#   apt_pkg.Config.Set("Debug::sourceList","1");
#   apt_pkg.Config.Set("Debug::pkgProblemResolver","1");
#   apt_pkg.Config.Set("Debug::pkgDPkgPM","1");
#   apt_pkg.Config.Set("Debug::pkgPackageManager","1");
#   apt_pkg.Config.Set("Debug::pkgDPkgProgressReporting","1");

  cache = apt.Cache(rootdir=TMP_DIR)
  cache.update()
  cache.open()

  pkgCache      = apt_pkg.Cache()
  depcache      = apt_pkg.DepCache(pkgCache)

# classes
class Package:
  dependsKey    = 'Depends'
  suggestsKey   = 'Suggests'
  recommendsKey = 'Recommends'

  basePackages  = ()
  
#  basePackages = ( 'libc6', 'debconf', 'libx11-6', 'xfree86-common',
#                   'debianutils', 'zlib1g', 'perl' )

  def __init__(self, name, version = None, arch = None, fileName = None):
    self.name     = name
    self.version  = version
    self.arch     = arch
    self.fileName = fileName
    
  def __str__(self):
    return "%s %s" % (self.name, self.version)
      
  def __hash__(self):
    return self.name.__hash__()

  def __eq__(self, p):
    if not type(self) == type(p):
      return False
    return (self.name == p.name and self.version == p.version)

class VersionedPackage(Package):

  def __init__(self, name, version = None, arch = None, fileName = None):
    Package.__init__(self, name, version, arch, fileName)

    # FIXME
    self.isVirtual    = False
    self.foundDeps    = False
    self.foundAllDeps = False

    if not self.version:
      try:
        self._package       = cache[name]
        self._versionObject = self._package.versions.get(0) # FIXME: JFC !!!
        self.version        = self._versionObject.version
        self.arch           = self._versionObject.architecture
        self.priority       = self._versionObject.priority
        try:
          self.isRequired  = self.priority == 'required'
          self.isImportant = self.priority == 'important'
          self.isStandard  = self.priority == 'standard'
        except KeyError:
          # sub-optimal, but some packages don't seem to have a 'Priority' key
          self.isRequired = self.isImportant = False
          self.isStandard = True

        self.fileName          = self._sanitizeName(self._versionObject.filename)
        self.fileNameWithEpoch = os.path.basename(self.fileName)
        try:
          self.fileNameWithEpoch = re.sub(r'_(.*?)_', '_%s_' % (self.version,), self.fileNameWithEpoch)
        except:
          pass

        self._versionedPackage = depcache.get_candidate_ver(pkgCache[self.name])
            
        packageFile = self._versionedPackage.file_list[0][0]
        indexFile = cache._list.find_index(packageFile)
        self.url = indexFile.archive_uri(self.fileName)
      except KeyError, AttributeError: # FIXME
#        print "ooops, couldn't find package %s" % self.name
        self.isVirtual = True
      except Exception, e:
        print "Exception while looking for %s: %s" % (self.name, e)
      
  def _sanitizeName(self, name):
    return name.replace('%3a', ':')

  def getName(self):
    return self.name

  def getVersionedPackage(self):
    return self._versionedPackage
  
  def getDependsList(self, extra = None):
    if self.foundDeps:
      return self.deps
    
    if self.isVirtual or self.isRequired: # or self.isImportant or self.isStandard:
      return []
    deps = self._versionedPackage.depends_list
    if self.dependsKey in deps:
#      self.deps = [ DepPackage(self.name) ]
      self.deps = []
#      print [ p for p in deps[dependsKey] ]
      intermediate = deps[self.dependsKey]
      if extra:
        if recommendsKey in deps:
          intermediate += deps[self.recommendsKey]
        if suggestsKey in deps:
          intermediate += deps[self.suggestsKey]
        
      for p in [ p[0] for p in intermediate ]:
        name = p.target_pkg.name
        if not name in Package.basePackages:
          self.deps.append(DepPackage(name, p.target_ver, p.comp_type))
#      print "%s --> %s" % (self.name, [ str(p) for p in self.deps ])
    else:
      self.deps = []

    self.foundDeps = True
    return self.deps

  def _getAllDeps(self, deps = set(), extra = None):
    for p in self.getDependsList(extra):
#      print "%s" % (p,)
      if not p in deps:
#        print "%s is a dep of %s" % (p, self)
        deps.add(p)
        for p1 in VersionedPackage(p.name)._getAllDeps():
          if not p1 in deps:
#            print "%s is a dep of %s" % (p, self)            
            deps.add(p1)

    return deps

  def getAllDeps(self):
    if self.isVirtual:
      return []
    if not self.foundAllDeps:
      # set extra to True to get recommends/suggest
      # FIXME: make this a CL option
      self.allDeps = self._getAllDeps(extra = None)
      self.allDeps.add(DepPackage(self.name))
#      print self.name
#      print DepPackage(self.name)
#      for p in self.allDeps:
#        print p.name
      self.foundAllDeps = True
    return self.allDeps

  def satisfies(self, depPkg):
    if not depPkg.comp:
      return True
    r = apt_pkg.VersionCompare(self.version, depPkg.version)
    result = apply( ops[depPkg.comp], (r,) )
#     print "compared package %s: %s to %s -> %s" % (depPkg.name,
#                                                    self.version,
#                                                    depPkg.version,
#                                                    result)
    return result
  
  def getURL(self):
    return self.url

  def download(self, name = None):
    if not name:
      name = self.fileNameWithEpoch
    print "%s --> %s" % (self.url, name)
    urllib.urlretrieve(self.url, name)
#    os.system("curl -o '%s' '%s'" % (name, self.url))
    print "download succeeded"

class DepPackage(Package):

  def __init__(self, name, version = None, comp = None):
    Package.__init__(self, name)
    self.version = version
    self.comp = comp

  def __str__(self):
    return "%s %s %s" % (self.name,
                         self.comp,
                         self.version)

  def __hash__(self):
    return self.__str__().__hash__()

  def __eq__(self, p):
    if not type(self) == type(p):
      return False
    elif self.name == p.name and self.comp == p.comp \
             and self.version == p.version:
      return True
    else:
      return False


class LocalPackages:
  reObj = re.compile(r'(.+?)_([^_]+)_([^\.]+)\.u?deb')

  def __init__(self, basedir):
    self.basedir = basedir
    self.pkgs = {}
    for root, dirs, files in os.walk(basedir):
      if root.count('/.svn'):
        continue
      for f in files:
        m = LocalPackages.reObj.match(f)
        if m and m.group(3) in ('all', ARCHITECTURE):
#          print "Found in store: %s (%s for %s)" % (m.group(1), m.group(2), m.group(3))
          self.pkgs[m.group(1)] = VersionedPackage(m.group(1),
                                                   m.group(2),
                                                   m.group(3),
                                                   os.path.join(root, f))

  def add(self, pkg):
    self.pkgs[pkg.name] = pkg

  def has(self, pkg):
    return pkg.name in self.pkgs

  def getByName(self, name):
    return self.pkgs[name]

  def getPkgs(self):
    return self.pkgs.values()

  def get(self, pkg):
    return self.pkgs[pkg.name]

  def __str__(self):
    s = ""
    for p in self.pkgs.values():
      s += "%s\n" % p
    return s[:-1]

import apt, apt_pkg, os, sys, urllib

def initializeChroot(TMP_DIR, sources, preferences):
  # FIXME
  global cache, pkgCache, depcache

  os.system('rm -fr ' + TMP_DIR)
  SOURCES    = TMP_DIR + '/sources.list'
  PREFS      = TMP_DIR + '/preferences'
  ARCHIVES   = TMP_DIR + '/archives'
  STATE      = TMP_DIR + '/varlibapt'
  LISTS      = STATE + '/lists'
  STATUS_DIR = TMP_DIR + '/varlibdpkg'
  STATUS     = STATUS_DIR + '/status'
  
  os.system('rm -fr ' + TMP_DIR)

  os.makedirs(TMP_DIR)
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

  apt_pkg.InitConfig()
  apt_pkg.InitSystem()
  apt_pkg.Config.Set("Dir::Etc::sourcelist", SOURCES)
  apt_pkg.Config.Set("Dir::Etc::preferences", PREFS)
  apt_pkg.Config.Set("Dir::Cache::archives", ARCHIVES)
  apt_pkg.Config.Set("Dir::State", STATE)
  apt_pkg.Config.Set("Dir::State::Lists",  LISTS)
  apt_pkg.Config.Set("Dir::State::status", STATUS)

  cache = apt.Cache()

  cache.update()
  cache.open(apt.progress.OpTextProgress())
  pkgCache      = apt_pkg.GetCache()
  depcache      = apt_pkg.GetDepCache(pkgCache)

# classes
class Package:
  dependsKey    = 'Depends'
  suggestsKey   = 'Suggests'
  recommendsKey = 'Recommends'

  basePackages  = ()
  
#  basePackages = ( 'libc6', 'debconf', 'libx11-6', 'xfree86-common',
#                   'debianutils', 'zlib1g', 'perl' )

  def __init__(self, name, version = None, fileName = None):
    self.name     = name
    self.version  = version
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

  def __init__(self, name, version = None, fileName = None):
    Package.__init__(self, name, version, fileName)

    # FIXME
    self.isVirtual               = False
    self.foundDeps             = False
    self.foundAllDeps          = False

    if not self.version:
      try:
        self._package          = cache[name]
        self._package._lookupRecord(True)
        self._record           = self._package._records.Record
        self._section          = apt_pkg.ParseSection(self._record)
        self.version           = self._section['Version']
        self.isRequired        = self._section['Priority'] == 'required'
        self.isImportant       = self._section['Priority'] == 'important'
        self.isStandard        = self._section['Priority'] == 'standard'
        self.fileName          = self._sanitizeName(self._section["Filename"])
        
        self._versionedPackage = depcache.GetCandidateVer(\
          pkgCache[self.name])
            
        packageFile = self._versionedPackage.FileList[0][0]
        indexFile = cache._list.FindIndex(packageFile)
        self.url = indexFile.ArchiveURI(self.fileName)
      except KeyError: # FIXME
        print "ooops, couldn't find package %s" % self.name
        self.isVirtual = True

  def _sanitizeName(self, name):
    return name.replace('%3a', ':')

  def getName(self):
    return self.name

  def getVersionedPackage(self):
    return self._versionedPackage
  
  def getDependsList(self, extra = None):
    if self.foundDeps:
      return self.deps
    
    if self.isVirtual or self.isRequired or self.isImportant or self.isStandard:
      return []
    deps = self._versionedPackage.DependsList
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
        name = p.TargetPkg.Name
        if not name in Package.basePackages:
          self.deps.append(DepPackage(name, p.TargetVer, p.CompType))
#      print "%s --> %s" % (self.name, [ str(p) for p in self.deps ])
    else:
      self.deps = []

    self.foundDeps = True
    return self.deps

  def _getAllDeps(self, deps = set(), extra = None):
    for p in self.getDependsList(extra):
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
    print "compared package %s: %s to %s -> %s" % (depPkg.name,
                                                   self.version,
                                                   depPkg.version,
                                                   result)
    return result
  
  def getURL(self):
    return self.url

  def download(self, name = None):
    if not name:
      name = os.path.basename(self.fileName)      
    print "%s --> %s" % (self.url, name)
    urllib.urlretrieve(self.url, name)

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
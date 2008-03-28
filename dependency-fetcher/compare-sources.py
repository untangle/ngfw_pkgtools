import apt, apt_pkg, commands, os.path, re, sys, urllib
import optparse

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "lib"))
import aptchroot

# constants
TMP_DIR = '/tmp/foo'
SOURCE = "deb http://%s/public/%s %s main premium upstream"
SVN_LOG = "svn log -r %s:%s svn://chef/%s"
MSG1 = 'r%s,svn://chef/%s,%s,,\n'
MSG2 = ',,,%s,http://bugzilla.untangle.com/show_bug.cgi?id=%s\n'
reUntangle = re.compile(r'untangle')
reSplitter = re.compile(r'\n-+\n', re.MULTILINE)
reExtract = re.compile(r'^r(\d+) \| (.*?) .*?closes:\s*(?:bug)?\s*\#\s*(\d+)(?:,\s*(?:bug)?\s*\#\s*(\d+))?.*?', re.MULTILINE | re.DOTALL | re.IGNORECASE)
reRevision = re.compile('.+svn.+r(\d+).+')

# functions
def getVersion(name):
  return aptchroot.VersionedPackage(name).version

def getRevisionFromVersion(version):
  return reRevision.sub(r'\1', version)

def getHighestRevisionFromSource(source):
  aptchroot.initializeChroot(TMP_DIR, source, "")
  v = [ getVersion(name)
        for name in aptchroot.cache.keys()
        if reUntangle.search(name) ]
  return getRevisionFromVersion(max(v))

def getSVNLog(revs, name):
  return commands.getoutput(SVN_LOG % tuple(revs+[name,]))

def getClosedBugs(st, name):
  result = ""
  for log in reSplitter.split(st):
    m = reExtract.match(log)
    if m:
      tup = m.groups()
      result += MSG1 % (tup[0], name, tup[1])
      for e in tup[2:]:
        if e:
          result += MSG2 % (e, e)
  return result

def writeToFile(s, fileName):
  f = open(fileName, 'a')
  f.write(str(s))
  f.close()

# main
if not len(sys.argv) == 4:
  usage()
  
revArgs = sys.argv[1:3]
fileBase = sys.argv[3]

txtFile = fileBase + ".txt"
csvFile = fileBase + ".csv"

for f in txtFile,csvFile:
  if os.path.isfile(f):
    print "%s already exist, aborting" % (f,)
    sys.exit(1)

revs = []
sources = []

for arg in revArgs:
  if re.search(r',', arg):
    source = SOURCE % tuple(arg.split(","))
    rev = getHighestRevisionFromSource(source)
  else:
    source = None
    rev = arg
  revs.append(rev)
  sources.append(source)

work = getSVNLog(revs, "work")
hades = getSVNLog(revs, "hades")

writeToFile('%s\n%s\n\n' % (sources,revs), txtFile)
writeToFile(work, txtFile)
writeToFile(hades, txtFile)

writeToFile('%s\n%s\n\n' % (sources,revs), csvFile)
writeToFile(getClosedBugs(work, "work"), fileBase + ".csv")
writeToFile(getClosedBugs(hades, "hades"), fileBase + ".csv")

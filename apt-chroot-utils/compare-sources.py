import apt, apt_pkg, commands, os, os.path, re, sys, urllib
import optparse

from lib import aptchroot

# constants
TMP_DIR = os.tmpnam()
SOURCE = "deb http://%s/public/%s %s main premium upstream"
SVN_LOG = "svn log -r %s:%s svn://chef/%s"
MSG1 = 'r%s,svn://chef/%s,%s,,\n'
MSG2 = ',,,%s,http://bugzilla.untangle.com/show_bug.cgi?id=%s\n'
reUntangle = re.compile(r'untangle')
reSplitter = re.compile(r'\n?-+\n', re.MULTILINE)
reExtract = re.compile(r'^r(\d+) \| (.*?) .*?closes:\s*(?:bug)?\s*\#\s*(\d+)(?:,\s*(?:bug)?\s*\#\s*(\d+))?.*?', re.MULTILINE | re.DOTALL | re.IGNORECASE)
reRevision = re.compile('.+svn.+r(\d+)(.+)-\d[a-z]+$')

# functions
def usage():
  print "compare-sources.py host1,repository1,distribution1 host2,repository2,distribution2 filebase"
  sys.exit(1)
  
def getVersion(name):
  return aptchroot.VersionedPackage(name).version

def getRevisionAndBranchFromVersion(version):
  rev, branch = reRevision.match(version).groups()
  if branch == 'trunk':
    branch = ''
  return rev, branch

def getHighestRevisionAndBranchFromSource(source):
  aptchroot.initializeChroot(TMP_DIR, source, "")
  # versions for all the untangle-* packages
  v = [ getVersion(name)
        for name in aptchroot.cache.keys()
        if reUntangle.search(name) ]
  return getRevisionAndBranchFromVersion(max(v))

def getSVNLog(revs, name):
  s = SVN_LOG % tuple(revs+[name,])
  print s
  return commands.getoutput(s)

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

revs     = []
sources  = []
branches = set()

for arg in revArgs:
  if re.search(r',', arg):
    source = SOURCE % tuple(arg.split(","))
    rev, branch = getHighestRevisionAndBranchFromSource(source)
    branches.add(branch)
  else:
    source = None
    rev = arg
  revs.append(rev)
  sources.append(source)

if len(branches) == 0:
  print "Couldn't determine the branch to run the diff for."
  exit(1)
elif len(branches) == 2:
  print "Those 2 sources are built from different branches (%s), can't run the diff." % (branches,)
  exit(1)

branch = branches.pop()
if not branch == "":
  branch = "branch/prod/%s" % (branch,)
branch = "%s/" % (branch,)

# FIXME: this is so fucked-up...
branch = branch.replace('release', 'release-')
branch = branch.replace('webui', 'web-ui')

work = getSVNLog(revs, branch + "work")
hades = getSVNLog(revs, branch + "hades")

writeToFile('%s\n%s\n\n' % (sources,revs), txtFile)
writeToFile(work, txtFile)
writeToFile(hades, txtFile)

writeToFile('%s\n%s\n\n' % (sources,revs), csvFile)
writeToFile(getClosedBugs(work, "work"), fileBase + ".csv")
writeToFile(getClosedBugs(hades, "hades"), fileBase + ".csv")

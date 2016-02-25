import apt, apt_pkg, commands, os, os.path, re, sys, urllib
import optparse

from lib import aptchroot

# constants
TMP_DIR = os.tmpnam()
SOURCE = "deb http://%s/public/%s %s main premium non-free upstream"
SVN_LOG = "svn log -r %s:%s https://untangle.svn.beanstalkapp.com/ngfw/%s"
MSG1 = 'r%s,https://untangle.svn.beanstalkapp.com/ngfw/%s,%s,,\n'
MSG2 = ',,,%s,http://bugzilla.untangle.com/show_bug.cgi?id=%s\n'
reUntangle = re.compile(r'untangle') # .+svn\d+r\d+')
reKernel = re.compile(r'(2\.6\.32|3\.2\.0|3\.16\.0)')
reSplitter = re.compile(r'\n?-+\n', re.MULTILINE)
reExtract = re.compile(r'^r(\d+) \| (.*?) .*?closes:\s*(?:bug)?\s*\#\s*(\d+)(?:,\s*(?:bug)?\s*\#\s*(\d+))?.*?', re.MULTILINE | re.DOTALL | re.IGNORECASE)
reRevision = re.compile('svn\d+r(\d+)(.+)-\d.+$')

# functions
def usage():
  print "compare-sources.py host1,repository1,distribution1 host2,repository2,distribution2 filebase"
  sys.exit(1)
  
def getVersion(name):
  return aptchroot.VersionedPackage(name).version

def validatePackage(name):
  return (reUntangle.search(name) and not reKernel.search(name))

def getRevisionAndBranchFromVersion(version):
  match = reRevision.search(version)
  if not match:
    return None, None
  rev, branch = match.groups()
  if branch in ('trunk', 'main'):
    branch = ''
  return rev, branch

def getHighestRevisionAndBranchFromSource(source):
  aptchroot.initializeChroot(TMP_DIR, source, "")
  # (rev, branch) for all the untangle-* packages
  l = [ getRevisionAndBranchFromVersion(getVersion(name))
        for name in aptchroot.cache.keys()
        if validatePackage(name) ]
  return sorted(l, key=lambda e: e[0])[-1]

def getSVNLog(revs, name):
  output = ""
  if revs[0] != revs[1]:
    revs = map(int, revs)
    revs.sort()
    command = SVN_LOG % (revs[0]+1, revs[1], name)
    output = commands.getoutput(command)
  return output

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

txtFile = fileBase + "_svn-changes.txt"
csvFile = fileBase + "_closed-bugs.csv"

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
  branch = "branch/%s" % (branch,)
branch = "%s/" % (branch,)

# FIXME: this is so fucked-up...
branch = branch.replace('release', 'release-')

work = getSVNLog(revs, branch + "work")
hades = getSVNLog(revs, branch + "hades")

writeToFile('%s\n%s\n\n' % (sources,revs), txtFile)
writeToFile(work, txtFile)
writeToFile(hades, txtFile)

writeToFile('%s\n%s\n\n' % (sources,revs), csvFile)
writeToFile(getClosedBugs(work, "work"), csvFile)
writeToFile(getClosedBugs(hades, "hades"), csvFile)

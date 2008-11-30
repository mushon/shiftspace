#!/usr/bin/python

# Reads the file/package metadata information which was created by corebuilder
# and preprocesses ShiftSpace.js into shiftspace.user.js

#import json # only available in Python >= 2.6 
import os
import sys
import re
import getopt
import simplejson as json # need to install simplejson from here http://pypi.python.org/pypi/simplejson/

# Exceptions ==============================

class SSError(Exception): 
  def __init__(self, builder, message = ''):
    self.message = message

  def __str__(self):
    return self.message

# FIXME: this file needs some serious optimization - David
class SSPreProcessor:

  INCLUDE_PACKAGE_REGEX = re.compile('^\s*//\s*INCLUDE PACKAGE\s+(\S+)\s*$');
  INCLUDE_REGEX = re.compile('^\s*//\s*INCLUDE\s+(\S+)\s*$');

  def setEnvVars(self, line):
    if self.envData != None:
      vars = ""
      for key in self.envData['data'].keys():
        if key != "VARS":
          line = line.replace(("%%%%%s%%%%" % (key)), '%s' % self.envData['data'][key])
        else:
          vars = "\n".join([("var %s = %s;" % (k, json.dumps(v))) for k,v in self.envData['data']['VARS'].iteritems()])
      line = line.replace("%%SYSTEM_TABLE%%", self.envData['meta'])
      line = line.replace("%%ENV_NAME%%", self.envData['name'])
      line = line.replace("%%VARS%%", vars)
    return line
  

  def includeFile(self, incFilename):
    flen = len(incFilename);
    logline1 = "\nif (SSInclude != undefined) SSLog('Including %s...', SSInclude);\n" % incFilename 
    prefix = ("\n// Start %s " % incFilename) + (69 - flen) * '-' + "\n\n"
    postfix = ("\n\n// End %s " % incFilename) + (71 - flen) * '-' + "\n\n"
    logline2 = "\nif (SSInclude != undefined) SSLog('... complete.', SSInclude);\n"
  
    self.outFile.write(logline1)

    # get the real name, incFilename is the pathname
    realName = os.path.splitext(os.path.basename(incFilename))[0]

    if realName in self.proj['files']['remove']:
      self.outFile.write('// PROJECT OVERRIDE -- FILE NOT INCLUDED\n\n')
      return
        
    if self.proj['files']['replace'].has_key(realName):
      # get the path of the file
      incFilename = self.metadata['files'][realName]['path']
      self.outFile.write('// PROJECT OVERRIDE -- INCLUDING %s INSTEAD\n' % incFilename)
    
    self.outFile.write(prefix)

    incFile = open(incFilename)
    
    self.preprocessFile(incFile)

    self.outFile.write(postfix)
    self.outFile.write(logline2)
    self.outFile.write("\nif(__sysavail__) __sysavail__.files.push('%s');\n" % os.path.splitext(os.path.basename(incFilename))[0])
    incFile.close()


  def preprocessFile(self, file):
    for line in file:
      line = self.setEnvVars(line)
      
      mo = self.INCLUDE_PACKAGE_REGEX.match(line)
      if mo:
        package = mo.group(1)

        self.outFile.write('\n// === START PACKAGE [%s] ===\n' % package)
      
        if package in self.proj['packages']['remove']:
          self.outFile.write('// PROJECT OVERRIDE -- PACKAGE NOT INCLUDED\n\n')
          continue
        
        if self.proj['packages']['replace'].has_key(package):
          package = self.proj['packages']['replace'][package]
          self.outFile.write('// PROJECT OVERRIDE -- INCLUDING PACKAGE %s INSTEAD\n' % package)
        
        # update the available packages dictionary
        self.outFile.write('\nif(__sysavail__) __sysavail__.packages.push("%s");\n' % package)

        # bail! no such package
        if not self.metadata['packages'].has_key(package):
          self.missingFileError(package)

        for component in self.metadata['packages'][package]:
          self.includeFile(self.metadata['files'][component]['path'])

        self.outFile.write('\n// === END PACKAGE [%s] ===\n\n' % package)
      else:
        mo = self.INCLUDE_REGEX.match(line)
        if mo:
          incFilename = mo.group(1)
        
          # bail! no such file
          if not self.metadata['files'].has_key(incFilename):
            self.missingFileError(incFilename)

          self.includeFile(self.metadata['files'][incFilename]['path'])
        else:
          self.outFile.write(self.setEnvVars(line))
  

  def missingFileError(self, package):
    print "Error: no such package %s exists, perhaps you forgot to run corebuilder.py first?" % package
    sys.exit(2)


  def usage(self):
      print "Usage: python preprocess.py <environment definition> [<project>] [<input file>]"
      print "  -h help"
      print "  -e environment file, this must be in SHIFTSPACE_DIR/config/env/"
      print "  -p project, defaults to shiftspace.json, must be in SHIFTSPACE_DIR/config/proj/"
      print "  -i input file, defaults to SHIFTSPACE_DIR/client/ShiftSpace-0.5.js"
      print "  -o output file, if none specified, writes to standard output" 


  def main(self, argv):
    # defaults
    proj = "shiftspace"
    outFile = None
    inFile = None
    envFileOption = None

    try:
      opts, args = getopt.getopt(argv, "hp:i:o:e:", ["environment=", "project=", "output=", "input=", "help", "project"])
    except getopt.GetoptError:
      self.usage()
      sys.exit(2)

    # parse arguments
    for opt, arg in opts:
      if opt in ("-h", "--help"):
        self.usage()
        sys.exit()
      elif opt in ("-p", "--project"):
        proj = arg
      elif opt in ("-o", "--output"):
        outFile = arg
      elif opt in ("-i", "--input"):
        inFile = arg
      elif opt in ("-e", "--environment"):
        envFileOption = arg
      else:
        assert False, "unhandled options"
        
    # get the metadata
    metadataJsonFile = open('../config/packages.json')
    metadataStr = metadataJsonFile.read()
    self.metadata = json.loads(metadataStr)
    metadataJsonFile.close()

    # get the input file
    if inFile != None:
      try:
        self.inFile = open(inFile)
      except IOError:
        # bail!
        print "Error: no such input file exist"
        sys.exit(2)
    else:
      self.inFile = open('../client/ShiftSpace-0.5.js')

    # get the output file
    if outFile != None:
      self.outFile = open(outFile, "w")
    else:
      self.outFile = sys.stdout
  
    # load environment file
    envFile = None
    evnFileName = None
    envFilePath = '../config/env/%s.json' % (os.path.splitext(envFileOption)[0])

    try:
      # load environment file
      envFile = open(envFilePath)
      envFileName = argv[0]
      env = json.loads(envFile.read())
      envFile.close()
      self.envData = {"name": envFileName, "data": env, "meta": metadataStr}
    except IOError:
      # bail!
      print "Error: no such environment file exists. (%s)" % envFilePath
      sys.exit(2)
    
    projFilePath = '../config/proj/%s.json' % (os.path.splitext(proj)[0])
    try:
      # load project file
      projFile = open(projFilePath)
      self.proj = json.loads(projFile.read())
      projFile.close()
    except IOError:
      # bail!
      print "Error: no such project file exists. (%s)" % projFilePath
      sys.exit(2)

    self.preprocessFile(self.inFile)
    
    self.outFile.close()
    self.inFile.close()

  
if __name__ == "__main__":
  preprocessor = SSPreProcessor()
  preprocessor.main(sys.argv[1:])
  pass
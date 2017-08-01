# Copyright 2017 Battelle Energy Alliance, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on July 5th, 2017 

@author: rouxpn 
"""
from __future__ import division, print_function, unicode_literals, absolute_import
import warnings
warnings.simplefilter('default',DeprecationWarning)

import os
import copy
import shutil
import re
from  __builtin__ import any as bAny
from CodeInterfaceBaseClass import CodeInterfaceBase
import phisicsdata
import xml.etree.ElementTree as ET
import tarfile


class Phisics(CodeInterfaceBase):
  """
    this class is used a part of a code dictionary to specialize Model.Code for RELAP5-3D Version 4.0.3
  """
  
  def getPath(self):
    """
      Retriever for path.
      @ In, None
      @ Out, __path, string, path
    """
    return self.__path
    
  def getBase(self):
    """
      Retriever for file base.
      @ In, None
      @ Out, __base, string path
    """
    return self.__base
    
    
  def copyIntoFolders(self, workDir):
    """
      copies the perturbed files into the their original directory. For example, BetaDecay.path belong to the relative folders
      ./path/BetaDecay.path
    """
    #print (workDir)
    os.rename(workDir+'/BetaDecay.path', workDir+'/path/BetaDecay.path')
    
  
  def untarFolders(self, tarName, workDir):
    """
      zip the folder need in PHISICS, copy the zipped files (path, library_fiss and input_dpl) in each perturbed folder and unzip there. 
    """
    t = tarfile.open(tarName, 'r')
    print (tarName) 
    f = t.extractall(workDir) 
    t.close()
    
  def tarFiles(self, directoryFiles):
    """
      gzip the folder needed in PHISICS, copy the zipped files (path, library_fiss and input_dpl) in each perturbed folder and unzip there. 
    """
    tarName = 'dirFiles.tar.gz'
    with tarfile.open(tarName, "w:gz") as mytar:
      for i in xrange(0,len(directoryFiles)):
        mytar.add(directoryFiles[i])
      mytar.add('ISOTXS000007')
    return tarName 
    
  def getDirInfo(self, driverXML):
    """
      get the working directory from the xml file
      In, XML file name 
      out, runInfoList, list. It contains the subdirectory name and number of perturbations
    """
    tree = ET.parse(driverXML)
    root = tree.getroot()
    for runInfoXML in root.getiterator('RunInfo'):
      for sequenceXML in runInfoXML.getiterator('Sequence'): 
        subdir =  sequenceXML.text
    for limitXML in root.getiterator('limit'):
      numberOfPert = limitXML.text
    #print (numberOfPert)
    runInfoList = [subdir, numberOfPert]
    return runInfoList
  
  def distributeVariablesToParsers(self, perturbedVars):
    """
      This module take the perturbedVars dictionary. perturbedVars contains all the variables to be perturbed. 
      The module transform the dictionary into dictionary of dictionary. This dictionary renders easy the distribution 
      of the variable to their corresponding parser. For example, if the two variables are the following: 
      {'FY|FAST|PU241|SE78':1.0, 'DECAY|BETA|U235':2.0}, the output dict will be: 
      {'FY':{'FY|FAST|PU241|SE78':1.0}, 'DECAY':{'DECAY|BETA|U235':2.0}}
      In: perturbVars, dictionary 
      out: distributedVars, dictionary of dictionary 
    """
    distributedPerturbedVars = {}
    pertType = []
    # teach what are the type of perturbation (decay FY etc...)
    for i in perturbedVars.iterkeys():
      splittedKeywords = i.split('|')
      pertType.append(splittedKeywords[0])
    # declare all the dictionaries according the different type of pert
    for i in xrange (0,len(pertType)):
      distributedPerturbedVars[pertType[i]] = {}
    # populate the dictionaries 
    for key, value in perturbedVars.items():
      splittedKeywords = key.split('|')
      for j in xrange (0,len(pertType)):
        if splittedKeywords[0] == pertType[j] :
          distributedPerturbedVars[pertType[j]][key] = value
    #print (distributedPerturbedVars)
    return distributedPerturbedVars
  
  def mapFile(self, driverXML):
    """
      This module map the "type" in the XML tree and locate, and associate the "type" value to a number. 
      this number is then used as an index to associate the correct files to be perturbed to the corresponding 
      parsers
      In: Driver input file (xml file)
      out: mapDict, dictionary, key is the "type", the value is a number
    """
    stepDict = {}
    fileDict = {}
    mapDict = {}
    stepCount = 0 
    tree = ET.parse(driverXML)
    root = tree.getroot()
    for stepsXML in root.getiterator('Steps'):
      for inputXML in stepsXML.getiterator('Input'): 
        #print (fileCount)
        #print (inputXML.attrib)
        #print (inputXML.text)
        stepDict[inputXML.text.lower()] = stepCount
        stepCount = stepCount + 1  
    for filesXML in root.getiterator('Files'):
      for inputXML in filesXML.getiterator('Input'): 
        fileDict[inputXML.attrib.get('type').lower()] = inputXML.text.lower()
    #for typeName, fileName in fileDict.item():
    #  for stepName, mapNumber in stepDict():
    mapDict = {k:stepDict[v] for k,v in fileDict.iteritems()}    
    #print (fileDict)
    #print (mapDict)
    return mapDict
  
  def addDefaultExtension(self):
    self.addInputExtension(['xml','dat','path'])
  
  def _readMoreXML(self,xmlNode):
    """
      Function to read the portion of the xml input that belongs to this specialized class and initialize
      some members based on inputs. This can be overloaded in specialize code interface in order to
      read specific flags.
      Only one option is possible. You can choose here, if multi-deck mode is activated, from which deck you want to load the results
      @ In, xmlNode, xml.etree.ElementTree.Element, Xml element node
      @ Out, None.
    """
    self.outputDeck = -1 # default is the last deck!
    for child in xmlNode:
      if child.tag == 'outputDeckNumber':
        try              : self.outputDeck = int(child.text)
        except ValueError: raise ValueError("can not convert outputDeckNumber to integer!!!! Got "+ child.text)

  def generateCommand(self,inputFiles,executable,clargs=None,fargs=None):
    """
      This method is used to retrieve the command (in tuple format) needed to launch the Code.
      See base class.  Collects all the clargs and the executable to produce the command-line call.
      Returns tuple of commands and base file name for run.
      Commands are a list of tuples, indicating parallel/serial and the execution command to use.
      @ In, inputFiles, list, List of input files (length of the list depends on the number of inputs have been added in the Step is running this code)
      @ In, executable, string, executable name with absolute path (e.g. /home/path_to_executable/code.exe)
      @ In, clargs, dict, optional, dictionary containing the command-line flags the user can specify in the input (e.g. under the node < Code >< clargstype =0 input0arg =0 i0extension =0 .inp0/ >< /Code >)
      @ In, fargs, dict, optional, a dictionary containing the axuiliary input file variables the user can specify in the input (e.g. under the node < Code >< clargstype =0 input0arg =0 aux0extension =0 .aux0/ >< /Code >)
      @ Out, returnCommand, tuple, tuple containing the generated command. returnCommand[0] is the command to run the code (string), returnCommand[1] is the name of the output root
    """
    #print (executable)
    found = False
    index = 0
    outputfile = 'out~'+inputFiles[index].getBase()
    #printprint (outputfile)
    if clargs: addflags = clargs['text']
    else     : addflags = ''
    #commandToRun = executable + ' -i ' + inputFiles[index].getFilename() + ' -o ' + outputfile  + '.o' + ' -r ' + outputfile  + '.r' + addflags
    #commandToRun = executable + ' -i ' + inputFiles[index].getFilename() + ' -o ' + outputfile  + '.o' +  addflags
    commandToRun = executable
    commandToRun = commandToRun.replace("\n"," ")
    commandToRun  = re.sub("\s\s+" , " ", commandToRun )
    #print (commandToRun)
    returnCommand = [('parallel',commandToRun)], outputfile
    #print (commandToRun)
    #print (returnCommand)
    return returnCommand
  
  def finalizeCodeOutput(self,command,output,workingDir):
    """
      This method is called by the RAVEN code at the end of each run (if the method is present, since it is optional).
      It can be used for those codes, that do not create CSV files to convert the whatever output format into a csv
      @ In, command, string, the command used to run the just ended job
      @ In, output, string, the Output name root
      @ In, workingDir, string, current working dir
      @ Out, output, string, optional, present in case the root of the output file gets changed in this method.
    """
    output = 'Dpl_INSTANT.outp-0'
    #print (command)
    #print (workingDir)
    #print (output) 
    #outfile = os.path.join(workingDir,output+'.o')
    outputobj=phisicsdata.phisicsdata(output, workingDir)
    #if outputobj.hasAtLeastMinorData(): outputobj.writeCSV(os.path.join(workingDir,output+'.csv'))
    #else: raise IOError('Relap5 output file '+ command.split('-o')[0].split('-i')[-1].strip()+'.o' + ' does not contain any minor edits. It might be crashed!')

  def checkForOutputFailure(self,output,workingDir):
    """
      This method is called by the RAVEN code at the end of each run  if the return code is == 0.
      This method needs to be implemented by the codes that, if the run fails, return a return code that is 0
      This can happen in those codes that record the failure of the job (e.g. not converged, etc.) as normal termination (returncode == 0)
      This method can be used, for example, to parse the outputfile looking for a special keyword that testifies that a particular job got failed
      (e.g. in RELAP5 would be the keyword "********")
      @ In, output, string, the Output name root
      @ In, workingDir, string, current working dir
      @ Out, failure, bool, True if the job is failed, False otherwise
    """
    from  __builtin__ import any as bAny
    failure = True
    errorWord = ["ERROR the number of materials in mat_map_to_instant block"]
    try   : outputToRead = open(os.path.join(workingDir,output+'.o'),"r")
    except: return failure
    readLines = outputToRead.readlines()
    for goodMsg in errorWord:
      if bAny(goodMsg in x for x in readLines):
        failure = False
        break
    
    
    failure = False
    return failure

  def createNewInput(self,currentInputFiles,oriInputFiles,samplerType,**Kwargs):
    """
      this generate a new input file depending on which sampler is chosen
      @ In, currentInputFiles, list,  list of current input files (input files from last this method call)
      @ In, oriInputFiles, list, list of the original input files
      @ In, samplerType, string, Sampler type (e.g. MonteCarlo, Adaptive, etc. see manual Samplers section)
      @ In, Kwargs, dictionary, kwarded dictionary of parameters. In this dictionary there is another dictionary called "SampledVars"
             where RAVEN stores the variables that got sampled (e.g. Kwargs['SampledVars'] => {'var1':10,'var2':40})
      @ Out, newInputFiles, list, list of newer input files, list of the new input files (modified and not)
    """ 
    import DecayParser
    import FissionYieldParser
    import QValuesParser
    import MaterialParser
    import PathParser
    
    keyWordDict = {}
    
    directoryFiles = ['path','library_fiss','input_dpl']
    #print (currentInputFiles)
    driverXML = 'test_phisics_code_interface.xml'
    keyWordDict = self.mapFile(driverXML)
    #print (keyWordDict)
    tarName = self.tarFiles(directoryFiles)
    runInfoList = self.getDirInfo(driverXML)
    #print (int(runInfoList[1]))
    N = int(runInfoList[1])
    
    
    #print (Kwargs)
    #print ("\n\n\n\n\n\n")
    perturbedVars = Kwargs['SampledVars']
    distributedPerturbedVars = self.distributeVariablesToParsers(perturbedVars)
    #print (distributedPerturbedVars)
    #perturbedVars = {'DECAY|BETA|U235':1.0778}
    #perturbedVars = {'FUEL1|DENSITY|U234':1.2, 'FUEL1|DENSITY|U235':1.08E+02}
    #perturbedVars = {'FY|FAST|PU241|SE78':1.2, 'FY|THERMAL|U238|ZN68':1.08E+02, 'FY|THERMAL|U235|ZN66':5.777}
    #perturbedVars = {'QVALUES|U235':4.5963, 'QVALUES|U238':1.08E+02, 'QVALUES|CF252':7.846}
    #perturbedVars = {'BETADECAY|U235':4.5963, 'BETADECAY|U238':1.08E+02, 'BETADECAY|CF252':7.846}
    
    # NOTE: IF YOU DON'T LIKE OR CAN'T GET THE THE KEYWORDS WIT THE DICTIONARY KEYWORDdICT, I CAN USE GETBASE TO 
    # OBRAIN THE KEYWORD CORRESPONDING TO THE PARSER OF INTEREST. EXAMPLE: AAA = currentInputFiles[0].getBase()print (AAA)
    for i in distributedPerturbedVars.iterkeys():
      if i == 'DECAY'    : decayParser        = DecayParser.DecayParser(currentInputFiles[keyWordDict['decay']].getAbsFile(), **distributedPerturbedVars[i])
      if i == 'DENSITY'  : materialParser     = MaterialParser.MaterialParser(currentInputFiles[keyWordDict['material']].getAbsFile(), **distributedPerturbedVars[i])
      if i == 'FY'       : FissionYieldParser = FissionYieldParser.FissionYieldParser(currentInputFiles[keyWordDict['fissionyield']].getAbsFile(), **distributedPerturbedVars[i])
      if i == 'QVALUES'  : QValuesParser      = QValuesParser.QValuesParser(currentInputFiles[keyWordDict['fissqvalue']].getAbsFile(), **distributedPerturbedVars[i])
      if i == 'BETADECAY': BetaDecayParser    = PathParser.PathParser(currentInputFiles[keyWordDict['betadecay']].getAbsFile(), **distributedPerturbedVars[i])
    
    tarFiles = currentInputFiles[keyWordDict['dirfiles']].getAbsFile()
    workDir = currentInputFiles[0].getPath()
    #print (workDir)
    self.untarFolders(tarFiles, workDir)
    self.copyIntoFolders(workDir)
    
    return currentInputFiles
    


import sys
import os
from ctypes import *
import re

pythonPath = str(sys.path[5]) + os.sep + 'FM_PAD.dll'

def InitSpecialInfo():
	path = pythonPath
	dll = CDLL(path)
	type703a = dll.GetGS703AFwTypeInt()
	if type703a == 1:
		dll.InitGS703A_FW_TYPE1()
	elif type703a == 2:
		dll.InitGS703A_FW_TYPE2()
	else:
		pass

def UperAndCmp(str1, str2):
	if str1.upper().find(str2) != -1:
		return 1
	else:
		return 0

def IsRecoveryImg(a): 
	return UperAndCmp(a,'RECOVERY.IMG:\\RAMDISK.IMG')

def IsProbatchImg(a): 
	return UperAndCmp(a,'R_PROBATCH')

def SaveRecoveryImg():
	path = pythonPath
	dll = CDLL(path)
	return dll.SaveRecoveryImg1()

def GenRecSaveData():
	path = pythonPath
	dll = CDLL(path)
	return dll.GenRecSaveData1()

def UnpackRecovery():
	ret = { 'ret' : '\\recovery.img'}
	return ret;

def SaveFile2Rec(lptszFilePath, pBuf, dwlen):
	path = pythonPath
	dll = CDLL(path)
	return dll.SaveFile2Rec1(lptszFilePath, pBuf, dwlen);

def GetScreenResolution(Height, Width):
	path = pythonPath
	dll = CDLL(path)
	return dll.GetScreenResolution1(Height,Width)

def ReplaceFileExEx(localfilePath, filename):
	path = pythonPath
	dll = CDLL(path)
	return dll.ReplaceFileExEx1(localfilePath,filename)

def UnpackRecoveryU():
	ret = {"argv0" : "\\ramdisk.img"}
	return ret

def GetDtbConfigFile(lpwConfigFile):
	path = pythonPath
	dll = CDLL(path)
	return dll.GetDtbConfigFile2(lpwConfigFile)

def SetDtbConfigFile(lpwszConfigPath, IErrorCode):
	path = pythonPath
	dll = CDLL(path)
	return dll.SetDtbConfigFile2(lpwszConfigPath, IErrorCode)

def GetScreenResolutionGS703A(Height, Width):
	path = pythonPath
	dll = CDLL(path)
	type703a = dll.GetGS703AFwTypeInt()
	if type703a == 3:
		return dll.GetScreenResolutionGS700D(Height, Width)
	else:
	    return dll.GetScreenResolutionGS703A2(Height,Width)

def GetScreenSizeNodeName():
	ret = { "argv0" : "hdmi@e02c0000"}
	return ret

def GetScreenSizeNodeNameWidthHeight():
	ret = { "argv0" : "panel@ghp", "argv1" : "draw_width", "argv2" : "draw_height"}
	return ret

def ParseBootInfoFile(lpwBootInfoFile, dBinSatrt, dBinLength, dMmcBinSatrt, dMmcBinLength, dDtbSatrt, dDtbLength, dDtbUpSatrt, dDtbUpLength, lpTextBase, lpUbootStart, dUbootBinUpLength):
	path = pythonPath
	dll = CDLL(path)
	return dll.ParseBootInfoFile1(lpwBootInfoFile, dBinSatrt, dBinLength, dMmcBinSatrt, dMmcBinLength, dDtbSatrt, dDtbLength, dDtbUpSatrt, dDtbUpLength, lpTextBase, lpUbootStart, dUbootBinUpLength)

def GetBootLogoEx(lpwBootLogoPath):
	path = pythonPath
	dll = CDLL(path)
	return dll.GetBootLogoEx1(lpwBootLogoPath)	

def SetBootLogoEx(lpwBootLogoPath, blIsChanged):
	path = pythonPath
	dll = CDLL(path)
	return dll.SetBootLogoEx1(lpwBootLogoPath, blIsChanged)

def CheckBootLogoFileIsPic(lpwFile):
	path = pythonPath
	dll = CDLL(path)
	return dll.CheckBootLogoFileIsPic1(lpwFile)

def GetProbatchImgCpio1():
	ret = {"argv0" : "\\r_probatch"}
	return ret

def GetProbatchImgCpio2(pBufferRaw, dwlen):
	path = pythonPath
	dll = CDLL(path)
	return dll.GetProbatchImgCpio21(pBufferRaw, dwlen)

def SaveProbatchImg1():
	ret = {"argv0" : "\\r_probatch"}
	return ret

def SaveProbatchImg2(pBootBin, dwBinlen):
	path = pythonPath
	dll = CDLL(path)
	return dll.SaveProbatchImg3(pBootBin, dwBinlen)

def SaveRamDisk():
	pass

def SearchFileFromProbatchImg():
	ret = {"argv0" : "r_probatch:"}
	return ret

def IsMultiConfiguration():
	return 0

def GetEditFileLocalPathEx(lpFileName, lpFilePath):
	path = pythonPath
	dll = CDLL(path)
	return dll.GetEditFileLocalPathEx1(lpFileName, lpFilePath)

def SetDtbConfigFileByDtsFile1(lpcwDtsFile, blLinuxPath):
	path = pythonPath
	dll = CDLL(path)
	return dll.SetDtbConfigFileByDtsFile211(lpcwDtsFile, blLinuxPath)

def SetDtbConfigFileByDtsFile2(szwMmcBootBinFile):
	path = pythonPath
	dll = CDLL(path)
	return dll.SetDtbConfigFileByDtsFile3(szwMmcBootBinFile)

def GetExportFileFromFw(wstr):
	return wstr.rfind("ramdisk.img:")

def CheckCpioFile(lpcwCpioFile, cpioType):
	return 1

def GetProbatchImgCpioUboot1():
	ret = {"argv0" : "\\r_probatch"}
	return ret

def GetProbatchImgCpioUboot2(pBufferRaw, dwlen):
	path = pythonPath
	dll = CDLL(path)
	return dll.GetProbatchImgCpioUboot3(pBufferRaw, dwlen)

def IsDtbFileLegal():
	path = pythonPath
	dll = CDLL(path)
	return dll.IsDtbFileLegal2()

def GetTemfolderPath(cfgFilePath):
	lastRegNum = cfgFilePath.rfind('\\')
	filePath = cfgFilePath[0:lastRegNum]
	lastRegNum = filePath.rfind('\\')
	filePath = filePath[0:lastRegNum]
	return filePath

def GetParnameFromIndex(filePath, index):
	parnameFilePath = filePath + "\\parname.ini"
	print "eee"
	if (os.path.isfile(parnameFilePath) == 0):
		parnameFilePath = GetTemfolderPath(parnameFilePath) + "\\parname.ini"
	f = open(parnameFilePath, "r")
	ret = "";
	while True:
		line = f.readline()
		if not line:
			break
		else :
			isFind = line.find(str(index))
			if isFind != -1:
				ret = line[isFind+len(str(index))+1:]
				break
	f.close()
	return ret

def GetParSizeFromCfgfile(filename, diskName):
	f = open(filename, "r")
	parSize = 0
	while True:
		line = f.readline()
		if not line:
			break
		elif (line.find(diskName) != -1) and (not line.startswith(";")):
			line = f.readline()
			line = f.readline()
			parSize = re.search(r'[-?\d]+', line).group(0)
			break 
	f.close()
	return parSize

def SetParSizeAccordingDiskName(filename, diskName, parSizeStr):
	f = open(filename, 'r')
	lines = f.readlines()
	f.close()
	f = open(filename, "w+")
	parSize = 0
	i = 0
	while i < len(lines):
		line = lines[i]
		if (line.find(diskName) != -1) and (not line.startswith(";")):
			f.write(line)
			line = lines[i+1]
			f.write(line)
			line = lines[i+2]
			i = i + 2
			rep = re.search(r'[-?\d]+', line).group(0)
			line = line.replace(str(rep),parSizeStr)
		f.write(line)
		i = i + 1
	f.close()
	return 1

def GetPartitionSizeEx(fileName, index, partitionSize):
	cfgFilePath = unicode(fileName)
	filePath = GetTemfolderPath(cfgFilePath)
	diskName = GetParnameFromIndex(filePath, index)
	parSize = GetParSizeFromCfgfile(cfgFilePath, diskName)

	parSizeBuf = c_buffer('\0', 520);
	parSizeStr = str(parSize)
	memmove(addressof(parSizeBuf), parSizeStr, len(parSizeStr));

	path = pythonPath
	dll = CDLL(path)
	#return dll.GetPartitionSizeEx2(fileName, index, partitionSize)
	return dll.SetMemAddressValue(partitionSize, parSizeBuf)

def SaveParSettingChange(binPath, idval, strParsize):
	cfgFilePath = unicode(binPath)
	filePath = GetTemfolderPath(cfgFilePath)
	diskName = GetParnameFromIndex(filePath, idval)
	parSizeStr = unicode(strParsize)

	return SetParSizeAccordingDiskName(cfgFilePath, diskName, parSizeStr)
	#path = pythonPath
	#dll = CDLL(path)
	#return dll.SaveParSettingChange3(binPath, idval, strParsize)

def SearchFileFromRecoveryImg():
	ret = {"argv0" : "ramdisk.img:"}
	return ret

def GetAndroidLogoImgName():
	ret = { 'argv0' : '\\ramdisk.img'}
	return ret;

def GetAndroidLogoImgNameEx():
	ret = { 'argv0' : '\\ramdisk.img:\\initlogo.rle'}
	return ret;

def GetMbrinfoFile():
	ret = { 'argv0' : 'partition.cfg'}
	return ret

def GetBootImgName():
	ret = { 'argv0' : 'ramdisk.img:'}
	return ret

def IsBootImg(a): 
	return UperAndCmp(a,'MISC.IMG:\\RAMDISK.IMG')

def uDisk():
	ret = { 'argv0' : 'UDISK'}
	return ret

def IsUDISKVailable():
	return 0

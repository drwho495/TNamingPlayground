import time
import math
import FreeCAD as App

class Timer:
    def __init__(self):
        self.startTimeMap = {}
        self.timeMap = {}
        self.pausedKeys = []
        self.pauseMap = {}
    
    def addKey(self, timeName, overwrite = False):
        if timeName not in self.timeMap or overwrite:
            self.startTimeMap[timeName] = time.time()
        else:
            self.resumeKey(timeName)
    
    def _flush(self, timeName, resetTimer = True):
        if timeName not in self.timeMap:
            self.timeMap[timeName] = 0
            
        self.timeMap[timeName] += time.time() - self.startTimeMap[timeName]
        if resetTimer: self.addKey(timeName, True)
    
    def getTime(self, timeName):
        if timeName in self.startTimeMap:
            if timeName not in self.pausedKeys:
                self._flush(timeName)
            
            if timeName in self.timeMap:
                return round(self.timeMap[timeName] * 1000, 1)
        return 0

    def getTotalTime(self):
        totalTime = 0

        for _, time in self.timeMap.items():
            totalTime += time
        
        return round(totalTime * 1000, 1)
    
    def pauseKeys(self):
        for key, _ in self.startTimeMap.items():
            self.pauseKey(key)

    def pauseKey(self, timeName):
        if timeName not in self.pausedKeys:
            self.pausedKeys.append(timeName)
            self._flush(timeName, False)

            if timeName not in self.pauseMap:
                self.pauseMap[timeName] = 0
            
            self.pauseMap[timeName] += 1
    
    def resumeKey(self, timeName):
        if timeName in self.pausedKeys:
            self.pausedKeys.pop(self.pausedKeys.index(timeName))
            self.addKey(timeName, True)
    
    def resumeKeys(self):
        self.pausedKeys = []
    
    def logKey(self, timeKey):
        if timeKey in self.startTimeMap:
            pauses = 0

            if timeKey in self.pauseMap:
                pauses = self.pauseMap[timeKey]

            App.Console.PrintLog(f"Time taken for {timeKey}: {self.getTime(timeKey)}, number of pauses: {pauses}\n")
    
    def logKeys(self):
        for key in self.startTimeMap:
            self.logKey(key)
    
    def removeKey(self, timeName):
        if timeName in self.startTimeMap:
            self.startTimeMap.pop(timeName)
        
        if timeName in self.timeMap:
            self.timeMap.pop(timeName)
        
        self.resumeKey(timeName)

    def removeKeys(self):
        self.startTimeMap = {}
        self.timeMap = {}
        self.pausedKeys = []
        self.pauseMap = {}

GlobalTimer = Timer()
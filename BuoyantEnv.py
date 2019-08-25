import subprocess
import sys
import time
from pathlib import Path
if sys.platform == "darwin":
    from AppKit import NSWorkspace
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGWindowListOptionIncludingWindow,
        kCGNullWindowID
    )
import numpy as np
import cv2
import pyautogui

class BuoyantEnv():
    def __init__(self):
        self.osType = sys.platform
        self.windowNumber = None
        self.appName = "Buoyant"

    def _launchProgram(self):
        if self.osType == "darwin":
            pathToApp =  str(Path.home()) + "/Library/Application Support/Steam/steamapps/common/Buoyant/Buoyant.app"
            print(pathToApp)
            retcode = subprocess.call(['open', '-a', pathToApp])
            print(retcode)
        if retcode != 0:
            raise Exception("Could not find" + self.appName + "!")

    def _getWindow(self):
        return CGWindowListCopyWindowInfo(
            kCGWindowListOptionIncludingWindow, 
            self.windowNumber
        )[0]

    def getCoordinates(self):
        coord = self._getWindow()['kCGWindowBounds']
        return (
            coord["X"], 
            coord["Y"], 
            coord["X"] + coord["Width"], 
            coord["Y"] + coord["Height"]
        )

    def _getListOfAttribute(
        self,
        options=kCGWindowListOptionOnScreenOnly,
        relativeToWindow=kCGNullWindowID
        ):
        return CGWindowListCopyWindowInfo(options, relativeToWindow)

    def _findWindowByPid(self, pid):
        if self.windowNumber != None:
            return 
        print('Finding window number...')
        window = None
        windowList = self._getListOfAttribute()
        pidList = [app['kCGWindowOwnerPID'] for app in windowList]
        if pid in pidList:
            window = windowList[pidList.index(pid)]
            return window['kCGWindowNumber']
        return None

    def _findWindowByName(self):
        if self.windowNumber != None:
            return 
        print('Finding window number...')
        window = None
        windowList = self._getListOfAttribute()
        names = [app['kCGWindowName'] for app in windowList] 
        if self.appName in names:
            window = windowList[names.index(self.appName)]
            return window['kCGWindowNumber']
        return None
    
    def _getPid(self):
        active_app_name = None
        app_pid = None
        print('Getting pid...')
        # Wait until application is frontmost
        while active_app_name != self.appName: 
            apps = NSWorkspace.sharedWorkspace().runningApplications()
            for app in apps:
                active_app_name = app.localizedName()
                print(active_app_name)
                app_pid = app.processIdentifier()
        return app_pid

    def _searchAndGetWindow(self, byType="pid"):
        """Poll for the window number"""
        while self.windowNumber == None:
            if byType == 'pid':
                pid = self._getPid()
                self.windowNumber = self._findWindowByPid(pid)
            elif byType == 'name':
                self.windowNumber = self._findWindowByName()

    def _translateCoordinates(self, x, y):
        coords = self.getCoordinates()
        return (coords[0] + x, coords[1] + y)

    def moveMouse(self, x, y):
        coords = self._translateCoordinates(x, y)
        pyautogui.moveTo(coords[0], coords[1])

    def getWindowShot(self, region=None):
        if region == None:
            region = self.getCoordinates()
        coord = (region[:])
        print(coord)
        img = pyautogui.screenshot(region=region)
        img = np.array(img)
        return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

    def getProgram(self):
        if sys.platform == "darwin":
            if self.windowNumber != None:
                return 
            self._launchProgram()
            self._searchAndGetWindow(byType='name')
            geometry = self.getCoordinates()
            print(geometry)
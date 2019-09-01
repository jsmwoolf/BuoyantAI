import subprocess
import sys
import time
from pathlib import Path
if sys.platform == "darwin":
    from AppKit import NSWorkspace, NSRunningApplication, NSApplicationActivateIgnoringOtherApps
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGWindowListOptionIncludingWindow,
        kCGNullWindowID
    )
elif sys.platform == "win32" or sys.platform == "cygwin":
    import win32gui
    import os
import numpy as np
import cv2
import pyautogui
import pytesseract

def showImage(title, img):
    cv2.imshow(title, img)
    cv2.waitKey(0)

class BuoyantEnv():
    def __init__(self):
        self.osType = sys.platform
        self.windowNumber = None
        self.appName = "Buoyant"
        self._onMenu = False

    def _launchProgram(self):
        if self.osType == "darwin":
            pathToApp =  str(Path.home()) + "/Library/Application Support/Steam/steamapps/common/Buoyant/Buoyant.app"
            print(pathToApp)
            retcode = subprocess.call(['open', '-a', pathToApp])
            print(retcode)
            if retcode != 0:
                raise Exception("Could not find" + self.appName + "!")
        elif self._isWindowsOS():
            steamPath = "C:\Program Files (x86)\Steam\steamapps\common\Buoyant"
            if os.path.isdir(steamPath):
                os.system('"C:\Program Files (x86)\Steam\Steam.exe" steam://rungameid/1085280')
            else:
                raise "Steam or the game isn't installed."
    
    def _isWindowsOS(self):
        return self.osType == "win32" or self.osType == "cygwin"

    def bringWindowToForeground(self):
        if self.osType == "darwin":
            app = NSRunningApplication.runningApplicationWithProcessIdentifier_(self._getWindow()['kCGWindowOwnerPID'])
            app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

    def _getWindow(self):
        return CGWindowListCopyWindowInfo(
            kCGWindowListOptionIncludingWindow, 
            self.windowNumber
        )[0]

    def getCoordinates(self):
        x, y, w, h = 0, 0, 0, 0
        if self.osType == 'darwin':
            coord = self._getWindow()['kCGWindowBounds']
            x = coord["X"]
            y = coord["Y"]
            w = coord["Width"]
            h = coord["Height"]
        elif self._isWindowsOS():
            coord = win32gui.GetWindowRect(self.windowNumber)
            x = coord[0]
            y = coord[1]
            w = coord[2] - x 
            h = coord[3] - y
        return (x, y, w, h)

    def _getBoundaries(self):
        x, y, w, h = 0, 0, 0, 0
        if self.osType == 'darwin':
            coord = self._getWindow()['kCGWindowBounds']
            x = coord["X"]
            y = coord["Y"]
            w = x + coord["Width"]
            h = y + coord["Height"]
        elif self._isWindowsOS():
            coord = win32gui.GetWindowRect(self.windowNumber)
            x = coord[0]
            y = coord[1]
            w = coord[2]
            h = coord[3]
        return (x, y, w, h)

    # _getListOfAttributes is a Mac OS X specific method.
    if sys.platform == 'darwin':
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
        if self.osType == 'darwin':
            windowList = self._getListOfAttribute()
            names = [app['kCGWindowName'] for app in windowList] 
            if self.appName in names:
                window = windowList[names.index(self.appName)]
                return window['kCGWindowNumber']
        elif self._isWindowsOS():
            time.sleep(5)
            hwnd = win32gui.FindWindow(None, "Buoyant")
            if hwnd != 0:
                return hwnd
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
        """Poll for the window number"""
        coords = self.getCoordinates()
        return (coords[0] + x, coords[1] + y)

    def moveMouse(self, x, y, duration=0, tween=pyautogui.linear):
        """Move the mouse to a specific part of the window"""
        coords = self._translateCoordinates(x, y)
        pyautogui.moveTo(coords[0], coords[1], duration=duration, tween=tween)

    def clickMouse(self):
        """Perform a left click"""
        pyautogui.click()

    def getWindowShot(self, region=None):
        if region == None:
            region = self.getCoordinates()
        coord = (region[:])
        print(coord)
        img = pyautogui.screenshot(region=region)
        img = np.array(img)
        return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

    def getProgram(self):
        if self.windowNumber != None:
            return 
        self._launchProgram()
        self._searchAndGetWindow(byType='name')
        geometry = self._getBoundaries()
        print(geometry)

    def isOnMenu(self):
        # 33, 445
        if self._onMenu:
            return True
        photo = self.getWindowShot()
        gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
        gray = gray[430:475 , 33: 90]
        gray[gray < 240] = 0
        gray[gray >= 240] = 255
        #showImage("Text", canny)
        text = pytesseract.image_to_string(gray).strip()
        print(text, ": ", len(text))

        if text.lower() == 'play':
            self._onMenu = True
            self.bringWindowToForeground()
        return self._onMenu

    def startGame(self):
        if self.isOnMenu():
            print("Start a game!")
            #print(x, y)
            self.moveMouse(62,450, duration = 0.5)
            time.sleep(0.5)
            self.clickMouse()
            self.onMenu = False
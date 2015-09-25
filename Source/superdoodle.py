# airdraw.py

import threading
import thread
import cv2,cv
import wx                  # This module uses the new wx namespace
import wx.html
from wx.lib import buttons # for generic button classes
from doodle import DoodleWindow
import icon
import os, cPickle
from numpy.core.numeric import dtype
from win32api import GetSystemMetrics
from numpy.lib.scimath import sqrt
import numpy as np
import win32api as api
import win32con as con
import back

element_erode=cv2.getStructuringElement(cv2.MORPH_ERODE, (3,3))
element_dilate=cv2.getStructuringElement(cv2.MORPH_DILATE, (3,3))

GREEN_MIN = np.array([50, 70,70],np.uint8)
GREEN_MAX = np.array([70, 255, 255],np.uint8)

screen_width=api.GetSystemMetrics (0)
screen_height=api.GetSystemMetrics (1)

baseMouseSensitivity=10

scale_x,scale_y=4,4
x1,y1=screen_width/2,screen_height/2
x1d,y1d=screen_width/2,screen_height/2
api.SetCursorPos((x1,y1))
count_undetected=0
count_detected=0

#----------------------------------------------------------------------
# There are standard IDs for the menu items we need in this app, or we
# could have used wx.NewId() to autogenerate some new unique ID values
# instead.

idNEW    = wx.ID_NEW
idOPEN   = wx.ID_OPEN
idSAVE   = wx.ID_SAVE
idSAVEAS = wx.ID_SAVEAS
idCLEAR  = wx.ID_CLEAR
idEXIT   = wx.ID_EXIT
idABOUT  = wx.ID_ABOUT

menu_MOVE_FORWARD  = wx.NewId() # Object menu items.
menu_MOVE_TO_FRONT = wx.NewId()
menu_MOVE_BACKWARD = wx.NewId()
menu_MOVE_TO_BACK  = wx.NewId()

ID_PENCIL=500
ID_RECT=502
ID_CIRCLE=501
ID_SPLINE=504
ID_LINE=503
ID_ELLIPSE=505
transparentbrush=wx.TRANSPARENT_BRUSH
transparentpen=wx.TRANSPARENT_PEN

class AdFrame(wx.Frame):
    """
    A AdFrame contains a DoodleWindow and a ControlPanel and manages
    their layout with a wx.BoxSizer.  A menu and associated event handlers
    provides for saving a doodle to a file, etc.
    """
    title = "AirDraw"
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, self.title, size=(1024,768),
                         style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE | wx.MAXIMIZE)

        self.SetIcon(icon.icon.GetIcon())
        self.CreateStatusBar()
        self.MakeMenu()
        self.MakeToolbar()
        self.filename = None
        self.doodle = DoodleWindow(self, -1)
        self.cPanel = ControlPanel(self, -1, self.doodle)
        colPanel=ColorPanel(self,-1,self.doodle)
        tpanel=ToolPanel(self,-1,self.doodle)



        self.Bind(wx.EVT_CLOSE,self.OnClose)
        vbox=wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(tpanel,0,wx.EXPAND)
        box.Add(self.doodle, 1, wx.EXPAND)
        box.Add(self.cPanel, 0, wx.EXPAND)
        vbox.Add(box,1,wx.EXPAND)
        vbox.Add(colPanel,0,wx.EXPAND)
        # Tell the frame that it should layout itself in response to
        # size events using this sizer.
        self.SetSizer(vbox)

    def OnClose(self,event):
        self.cPanel.CloseCam()
        self.Destroy()

    def SaveFile(self):
        if self.filename:
            file=self.filename
            temp=os.path.splitext(file)[1]
            name,extention=temp.split(('.'))
            if extention=="ad":

                data = self.doodle.GetLinesData()
                f = open(self.filename, 'w')
                cPickle.dump(data, f)
                f.close()
            elif extention=="bmp":
                data=self.doodle.GetBitmapData()
                data.SaveFile(self.filename, wx.BITMAP_TYPE_BMP)
                self.SetTitle("")

            elif extention=="png":
                data=self.doodle.GetBitmapData()
                data.SaveFile(self.filename, wx.BITMAP_TYPE_PNG)
                self.SetTitle("")

            elif extention=="jpg":
                data=self.doodle.GetBitmapData()
                data.SaveFile(self.filename, wx.BITMAP_TYPE_JPEG)
                self.SetTitle("")




    def ReadFile(self):
        if self.filename:
            try:
                f = open(self.filename, 'r')
                data = cPickle.load(f)
                f.close()
                self.doodle.SetLinesData(data)
            except cPickle.UnpicklingError:
                wx.MessageBox("%s is not a legal file." % self.filename,
                             "oops!", style=wx.OK|wx.ICON_EXCLAMATION)
    def MakeToolbar(self):

        artBmp = wx.ArtProvider.GetBitmap
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_3DBUTTONS)
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(
            wx.ID_NEW,  wx.Bitmap("./images/new.png", wx.BITMAP_TYPE_PNG), "New")
        self.toolbar.AddSimpleTool(
            wx.ID_OPEN,  wx.Bitmap("./images/open.png", wx.BITMAP_TYPE_PNG), "Open")
        self.toolbar.AddSimpleTool(
            wx.ID_SAVE,  wx.Bitmap("./images/save.png", wx.BITMAP_TYPE_PNG), "Save")
        self.toolbar.AddSimpleTool(
            wx.ID_SAVEAS,  wx.Bitmap("./images/saveas.png", wx.BITMAP_TYPE_PNG),
            "Save As...")
        self.toolbar.AddSimpleTool(
            wx.ID_UNDO,  wx.Bitmap("./images/back.png", wx.BITMAP_TYPE_PNG), "Undo")
        self.toolbar.AddSimpleTool(
            wx.ID_REDO,  wx.Bitmap("./images/front.png", wx.BITMAP_TYPE_PNG), "Redo")

        self.Bind(wx.EVT_MENU,   self.OnMenuOpen, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU,   self.OnMenuSave, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnMenuSaveAs, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU,  self.OnMenuClear, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU,  self.OnUndo, id=wx.ID_UNDO)
        self.Bind(wx.EVT_MENU,  self.OnRedo, id=wx.ID_REDO)
        self.toolbar.Realize()


    def MakeMenu(self):
        # create the file menu
        menu1 = wx.Menu()

        menu1.Append(idOPEN, "&Open\tCtrl-O", "Open a AirDraw file")
        menu1.Append(idSAVE, "&Save\tCtrl-S", "Save the AirDraw")
        menu1.Append(idSAVEAS, "Save &As", "Save the AirDraw in a new file")
        menu1.AppendSeparator()
        menu1.Append(idCLEAR, "&Clear", "Clear the current AirDraw")
        menu1.AppendSeparator()
        menu1.Append(idEXIT, "E&xit", "Terminate the application")

        menu2 = wx.Menu()
        menu2.Append(idABOUT, "&About\tCtrl-H", "Display")

        menuBar = wx.MenuBar()
        menuBar.Append(menu1, "&File")
        menuBar.Append(menu2, "&Help")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU,   self.OnMenuOpen, id=idOPEN)
        self.Bind(wx.EVT_MENU,   self.OnMenuSave, id=idSAVE)
        self.Bind(wx.EVT_MENU, self.OnMenuSaveAs, id=idSAVEAS)
        self.Bind(wx.EVT_MENU,  self.OnMenuClear, id=idCLEAR)
        self.Bind(wx.EVT_MENU,   self.OnMenuExit, id=idEXIT)
        self.Bind(wx.EVT_MENU,  self.OnMenuAbout, id=idABOUT)



    wildcard = "airdraw files (*.ad)|*.ad|Bitmap files (*.bmp)|*.bmp|JPEG files (*.jpg)|*.jpg|PNG files (*.png)|*.png|All files (*.*)|*.*"

    def OnMenuOpen(self, event):
        dlg = wx.FileDialog(self, "Open file...", os.getcwd(),
                           style=wx.OPEN, wildcard = self.wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
            self.ReadFile()
            self.SetTitle(self.title + ' -- ' + self.filename)
        dlg.Destroy()


    def OnMenuSave(self, event):
        if not self.filename:
            self.OnMenuSaveAs(event)
        else:
            self.SaveFile()


    def OnMenuSaveAs(self, event):
        dlg = wx.FileDialog(self, "Save as...", os.getcwd(),
                           style=wx.SAVE | wx.OVERWRITE_PROMPT,
                           wildcard = self.wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            if not os.path.splitext(filename)[1]:
                filename = filename + '.ad'
            self.filename = filename
            self.SaveFile()
            self.SetTitle(self.title + ' -- ' + self.filename)
        dlg.Destroy()


    def OnMenuClear(self, event):
        self.doodle.SetLinesData([])
        self.SetTitle(self.title)

    def OnUndo(self, e):
        temp=self.doodle.LinePop()
        if not temp:
            dial = wx.MessageDialog(None, 'No Undo', 'Info', wx.OK)
            dial.ShowModal()
            dial.Center()

    def OnRedo(self, e):

        temp=self.doodle.LinePush()
        if not temp:
            dial = wx.MessageDialog(None, 'No Redo', 'Info', wx.OK)
            dial.ShowModal()
            dial.Center()

    def OnMenuExit(self, event):
        self.OnClose(event)


    def OnMenuAbout(self, event):
        dlg = DoodleAbout(self)
        dlg.ShowModal()
        dlg.Destroy()

#----------------------------------------------------------------------

class ColorPanel(wx.Panel):




    BMP_SIZE = 25
    BMP_BORDER = 3

    def __init__(self, parent, ID, doodle):
        wx.Panel.__init__(self, parent, ID, style=wx.BORDER_DOUBLE, size=(20,20))
        self.SetBackgroundColour((190, 190, 190))
        numCols =8
        spacing = 4
        btnSize = wx.Size(self.BMP_SIZE + 2*self.BMP_BORDER,
                          self.BMP_SIZE + 2*self.BMP_BORDER)
        a=self.MakeBitmap('Black',50)
        self.cur=wx.StaticText(self,-1,'',size=(50,50),style=wx.BORDER_SIMPLE)
        self.cur.SetBackgroundColour('Black')




        self.clrBtns = {}
        colours = doodle.menuColours
        keys = colours.keys()
        keys.sort()
        cGrid = wx.GridSizer(cols=numCols, hgap=10, vgap=10)
        for k in keys:
            bmp = self.MakeBitmap(colours[k],self.BMP_SIZE)
            b = buttons.GenBitmapToggleButton(self, k, bmp, size=btnSize)
            b.SetBezelWidth(0)
            b.SetUseFocusIndicator(False)
            self.Bind(wx.EVT_BUTTON, self.OnSetColour, b)
            cGrid.Add(b, 0)
            self.clrBtns[colours[k]] = b




        doodle.Notify()
        self.doodle = doodle
        self.doodle.shape=0

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.cur,0,wx.ALL,2*spacing)
        box.AddSpacer(20)
        box.Add(cGrid, 0, wx.ALL, spacing)

        self.SetSizer(box)
        self.SetAutoLayout(True)
        box.Fit(self)


    def MakeBitmap(self, colour,size):




        bmp = wx.EmptyBitmap(size, size)
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.SetBackground(wx.Brush(colour))
        dc.Clear()
        dc.SelectObject(wx.NullBitmap)
        return bmp


    def OnSetColour(self, event):


        colour = self.doodle.menuColours[event.GetId()]
        if colour != self.doodle.colour:
            # untoggle the old colour button
            self.clrBtns[self.doodle.colour].SetToggle(False)

        # set the new colour
        self.doodle.SetColour(colour)
        self.cur.SetBackgroundColour(colour)
        self.cur.Refresh()
        self.clrBtns[colour].SetToggle(False)


#----------------------------------------------------------------------
class ToolPanel(wx.Panel):

    def __init__(self, parent, ID, doodle):
        wx.Panel.__init__(self, parent, ID, style=wx.BORDER_DOUBLE, size=(70,20))
        self.cur_ID=ID_PENCIL
        self.doodle=doodle

        self.SetBackgroundColour((190, 190, 190))
        cGrid = wx.GridSizer(cols=1, hgap=20, vgap=5)
        pencil=self.GetBitmapButton("scribble",ID_PENCIL)
        circle=self.GetBitmapButton("ellipse",ID_CIRCLE)
        rect=self.GetBitmapButton("rect",ID_RECT)
        stline=self.GetBitmapButton("line",ID_LINE)
        spline=self.GetBitmapButton("spline",ID_SPLINE)

        self.cur_tool_list={
        ID_PENCIL:(pencil,"scribble"),
        ID_CIRCLE:(circle,"ellipse"),
        ID_RECT:(rect,"rect"),
        ID_LINE:(stline,"line"),
        ID_SPLINE:(spline,"spline")
        }

        bmp=self.GetSelBitmap("scribble")
        pencil.SetBitmapLabel(bmp)
        pencil.Refresh()
        self.Bind(wx.EVT_BUTTON,self.OnToolSelect,pencil)
        self.Bind(wx.EVT_BUTTON,self.OnToolSelect,circle)
        self.Bind(wx.EVT_BUTTON,self.OnToolSelect,rect)
        self.Bind(wx.EVT_BUTTON,self.OnToolSelect,stline)
        self.Bind(wx.EVT_BUTTON,self.OnToolSelect,spline)

        cGrid.Add(pencil,1,border=5)
        cGrid.Add(circle,1,border=5)
        cGrid.Add(rect,1,border=5)
        cGrid.Add(stline,1,border=5)
        cGrid.Add(spline,1,border=5)

        box = wx.BoxSizer(wx.VERTICAL)
        box.AddSpacer(20)
        box.Add(cGrid,0,wx.EXPAND,border=10)
        self.SetSizer(box)
        self.SetAutoLayout(True)
        box.Fit(self)

    def GetBitmapButton(parent, iconName, ID):

        bmp=wx.Bitmap("./images/" + iconName + "Icon.bmp", wx.BITMAP_TYPE_BMP)
        bmpsel = wx.Bitmap("./images/" + iconName + "IconSel.bmp", wx.BITMAP_TYPE_BMP)
        b = buttons.GenBitmapButton(parent, ID, bmp, size=(bmp.GetWidth()+1, bmp.GetHeight()+1),
                        style=wx.BORDER_NONE)
        b.SetBezelWidth(0)
        b.SetForegroundColour((49,49,49))
        b.SetBitmapLabel(bmp)
        b.SetBitmapSelected(bmpsel)

        b.iconID     = ID
        b.iconName   = iconName

        return b

    def OnToolSelect(self,event):

        if self.cur_ID!=event.GetId():
            cur_button,var=self.cur_tool_list[self.cur_ID]
            bmp=self.GetUnselBitmap(var)
            cur_button.SetBitmapLabel(bmp)
            cur_button.Refresh()
            new_button,var2=self.cur_tool_list[event.GetId()]
            bmpsel=self.GetSelBitmap(var2)
            new_button.SetBitmapLabel(bmpsel)
            new_button.Refresh()
            self.cur_ID=event.GetId()
            self.SetCanvasTool(self.cur_ID)

    def SetCanvasTool(self,id):
        if id==ID_PENCIL:
            self.doodle.shape=0
            self.doodle.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))
        elif id==ID_CIRCLE:
            self.doodle.shape=1
            self.doodle.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        elif id==ID_RECT:
            self.doodle.shape=2
            self.doodle.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        elif id==ID_LINE:
            self.doodle.shape=3
            self.doodle.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        elif id==ID_SPLINE:
            self.doodle.shape=4
            self.doodle.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

    def GetSelBitmap(self,iconName):
        bmpsel = wx.Bitmap("./images/" + iconName + "IconSel.bmp", wx.BITMAP_TYPE_BMP)
        return bmpsel

    def GetUnselBitmap(self,iconName):
        bmp = wx.Bitmap("./images/" + iconName + "Icon.bmp", wx.BITMAP_TYPE_BMP)
        return bmp

class ControlPanel(wx.Panel):






    BMP_SIZE = 16
    BMP_BORDER = 3

    def __init__(self, parent, ID, doodle):
        wx.Panel.__init__(self, parent, ID, style=wx.BORDER_DOUBLE, size=(20,20))
        self.SetBackgroundColour((190, 190, 190))
        numCols = 4
        spacing = 5

        btnSize = wx.Size(self.BMP_SIZE + 2*self.BMP_BORDER,
                          self.BMP_SIZE + 2*self.BMP_BORDER)
        self.cam=Camera(self)


        hbox=wx.BoxSizer(wx.HORIZONTAL)
        self.sld = wx.Slider(self, value=1, minValue=1, maxValue=15, style= wx.SL_HORIZONTAL | wx.SL_LABELS,size=(300,45))
        self.sld.Bind(wx.EVT_SCROLL,self.OnSetThickness)
        hbox.Add(self.sld,0,wx.EXPAND|wx.ALL,spacing)


        ci = ColourIndicator(self)
        doodle.AddListener(ci)
        doodle.Notify()
        self.doodle = doodle


        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.cam,0,wx.EXPAND,spacing)
        box.Add(hbox, 0, wx.EXPAND|wx.ALL, spacing)
        box.Add(ci, 0, wx.EXPAND|wx.ALL, spacing)
        self.SetSizer(box)
        self.SetAutoLayout(True)
        box.Fit(self)

    def CloseCam(self):
        self.cam.CloseCam()

    def MakeBitmap(self, colour):

        bmp = wx.EmptyBitmap(self.BMP_SIZE, self.BMP_SIZE)
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.SetBackground(wx.Brush(colour))
        dc.Clear()
        dc.SelectObject(wx.NullBitmap)
        return bmp


    def OnSetColour(self, event):

        colour = self.doodle.menuColours[event.GetId()]
        if colour != self.doodle.colour:
            # untoggle the old colour button
            self.clrBtns[self.doodle.colour].SetToggle(False)
        # set the new colour
        self.doodle.SetColour(colour)


    def OnSetThickness(self, event):

        thickness = event.GetId()
        obj=event.GetEventObject()
        val=obj.GetValue()
        self.doodle.SetThickness(val)



#----------------------------------------------------------------------

class Camera(wx.Window):

    def __init__(self,parent):
        super(Camera,self).__init__(parent,-1,style=wx.SUNKEN_BORDER, size=(screen_width/4,screen_height/4))
        self.cam=cv2.VideoCapture(0)
        self.cam.set(cv.CV_CAP_PROP_FRAME_WIDTH, screen_width/4)
        self.cam.set(cv.CV_CAP_PROP_FRAME_HEIGHT, screen_height/4)
        ret, frame = self.cam.read()
        height, width = frame.shape[:2]
        parent.SetSize((width, height))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.bmp = wx.BitmapFromBuffer(width, height, frame)
        self.Display=wx.StaticBitmap(self,-1,self.bmp)
        hbox=wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.Display,0,wx.EXPAND)
        self.SetSizer(hbox)
        self.SetAutoLayout(True)
        self.timer = wx.Timer(self)
        self.timer.Start(1)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_TIMER, self.NextFrame)

        hbox.Fit(self)
    def OnPaint(self, evt):
        dc = wx.BufferedPaintDC(self)
        dc.DrawBitmap(self.bmp, 0, 0)


    def NextFrame(self, event):

        global x1,y1,x1d,y1d,count_undetected,count_detected
        detected=False
        self.ret, self.frame = self.cam.read()
        self.frame=cv2.flip(self.frame, flipCode=1)
        if self.ret:
            img_thresholded=self.GetThresholdedImage(self.frame);
            img_thresholded=cv2.erode(img_thresholded, element_erode)
            img_thresholded=cv2.dilate(img_thresholded, element_dilate)
            contours, hierarchy = cv2.findContours(img_thresholded,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(img_thresholded, contours, -1, (255,0,0))
            circle_contour=[]
            for i in range(len(contours)) :
                if len(contours[i])>15:
                    hull=cv2.convexHull(contours[i])
                    center=np.mean(hull, 0)
                    dist=np.array(np.linalg.norm(center-hull[0][0]),np.float64)
                    for j in range(len(hull)) :
                        dist=np.append(dist, np.array(np.linalg.norm(center-hull[j][0]),np.float64))
                        radius_dev=np.std(dist)
                    if radius_dev<3:
                        center=np.reshape(center, -1)
                        center=map(int,center)
                        circle_contour.append((center,radius_dev,np.mean(dist)))

            min_dev=None
            final_radius=None
            final_center=[]

            for center,dev,radius in circle_contour:
                if min_dev==None:
                    min_dev=dev
                    final_center=center
                    final_radius=radius
                elif min_dev>dev:
                    min_dev=dev
                    final_center=center
                    final_radius=radius

            if len(circle_contour)>0:
                if count_undetected!=0:
					x1d,y1d=final_center
					x1d*=scale_x
					y1d*=scale_y
					count_undetected=0
                x2d,y2d=final_center
                x2d*=scale_x
                y2d*=scale_y
                cv2.circle(self.frame,tuple(final_center) , int(final_radius), (255,0,0),-1)
                deltaX=int(x2d-x1d)
                deltaY=int(y2d-y1d)
                (deltaX,deltaY)=self.ActualDxDy(x1,y1,deltaX,deltaY)
                self.smoothMouseMove(deltaX,deltaY)
                x2=deltaX+x1
                y2=deltaY+y1
                x1d,y1d=x2d,y2d
                x1,y1=x2,y2
                count_detected+=1
                detected=True

            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            self.bmp.CopyFromBuffer(self.frame)
            self.Display.SetBitmap(self.bmp)
            self.Display.Refresh()
            self.Refresh()
        if detected==False:
            count_undetected+=1
            count_detected=0

    def GetThresholdedImage(self,img):
        img_HSV=cv2.cvtColor(img, cv2.COLOR_BGR2HSV);
        img_thresholded=cv2.inRange(img_HSV, GREEN_MIN, GREEN_MAX);
        return img_thresholded;

    def my_range(self,start, end, step):
        while start <= end:
            yield start
            start += step

    def scaleMouseSensitivity(self,deltaX ,deltaY):
        if abs(deltaX) <=5 and abs(deltaY) <=5 :
            return 0
        distance = sqrt(deltaX*deltaX + deltaY*deltaY);
        return baseMouseSensitivity / 2.0 * (2.0/(1 + pow(2.718,(0-distance/1.2)/60)) - 1)

    def ActualDxDy(self,x1,y1,deltaX,deltaY):
        spotSensitivity = self.scaleMouseSensitivity(deltaX, deltaY)
        a=api.GetAsyncKeyState(0x01)
        if a==1 :
            spotSensitivity=spotSensitivity/2
        movex = int(deltaX*spotSensitivity)
        movey = int(deltaY*spotSensitivity)
        return movex,movey


    def smoothMouseMove(self,movex,movey):
        for s in self.my_range(0,1,0.05) :
			api.SetCursorPos((int(x1 + movex*s) , int(y1 + movey*s)))

    def CloseCam(self):

        self.timer.Stop()
        self.timer.Destroy()
        cv2.VideoCapture(0).release()

#-----------------------------------------------------------------------
class ColourIndicator(wx.Window):


    def __init__(self, parent):
        wx.Window.__init__(self, parent, -1, style=wx.SIMPLE_BORDER)
        self.SetBackgroundColour(wx.WHITE)
        self.SetSize( (45, 40) )
        self.colour = self.thickness = None
        self.Bind(wx.EVT_PAINT, self.OnPaint)


    def Update(self, colour, thickness):

        self.colour = colour
        self.thickness = thickness
        self.Refresh()  # generate a paint event


    def OnPaint(self, event):


        dc = wx.PaintDC(self)
        if self.colour:
            sz = self.GetClientSize()
            pen = wx.Pen(self.colour, self.thickness)
            dc.BeginDrawing()
            dc.SetPen(pen)
            dc.DrawLine(10, sz.height/2, sz.width-10, sz.height/2)
            dc.EndDrawing()


#----------------------------------------------------------------------

class DoodleAbout(wx.Dialog):

    text = '''
<html>
<body bgcolor="#ACAA60">
<center><table bgcolor="#455481" width="100%" cellspacing="0"
cellpadding="0" border="1">
<tr>
    <td align="center"><h1>Air Draw</h1></td>
</tr>
</table>
</center>
<p><b>Air Draw</b> is a project developed in <b>Python</b> and <b>OpenCV</b> that
is used for free hand drawing on the a computer by moving an object in from of the the webcam
<br>
Instructions: </p>
<p>
<ol>
  <li>Hold the green circular object in front of the cam such that entire circle is visible to the webcam
  <li>When you see the blue circle operlapping the green one you can move it to see that mouse follows it
  <li>Select any tool and start AirDrawing
</ol>

<p><b>Air Draw</b> is brought to you by
<b>Ronak Parpani</b>,<b>Saurabh Netravalkar</b>,<b>Pooja Pai</b>, Copyright
&copy; 2013.</p>
</body>
</html>
'''

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About AirDraw',
                          size=(420, 380) )

        html = wx.html.HtmlWindow(self, -1)
        html.SetPage(self.text)
        button = wx.Button(self, wx.ID_OK, "Okay")

        # constraints for the html window
        lc = wx.LayoutConstraints()
        lc.top.SameAs(self, wx.Top, 5)
        lc.left.SameAs(self, wx.Left, 5)
        lc.bottom.SameAs(button, wx.Top, 5)
        lc.right.SameAs(self, wx.Right, 5)
        html.SetConstraints(lc)

        # constraints for the button
        lc = wx.LayoutConstraints()
        lc.bottom.SameAs(self, wx.Bottom, 5)
        lc.centreX.SameAs(self, wx.CentreX)
        lc.width.AsIs()
        lc.height.AsIs()
        button.SetConstraints(lc)

        self.SetAutoLayout(True)
        self.Layout()
        self.CentreOnParent(wx.BOTH)


#----------------------------------------------------------------------

class AirDrawApp(wx.App):
    def OnInit(self):
        frame = AdFrame(None)
        frame.Show(True)
        self.SetTopWindow(frame)
        return True


#----------------------------------------------------------------------
class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):
        app = AirDrawApp(redirect=True)
        app.MainLoop()

if __name__ == '__main__':
    gui= myThread(1, "Thread-1", 1)
    gui.run()

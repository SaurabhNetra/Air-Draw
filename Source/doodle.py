

import wx                  # This module uses the new wx namespace
import numpy as np
#----------------------------------------------------------------------

class DoodleWindow(wx.Window):
    menuColours = { 100 : 'Black',
                    101 : 'Yellow',
                    102 : 'Red',
                    103 : 'Green',
                    104 : 'Blue',
                    105 : 'Purple',
                    106 : 'Brown',
                    107 : 'Aquamarine',
                    108 : 'Forest Green',
                    109 : 'Light Blue',
                    110 : 'Goldenrod',
                    111 : 'Cyan',
                    112 : 'Orange',
                    113 : 'Navy',
                    114 : 'Dark Grey',
                    115 : 'Light Grey',
                    }
    maxThickness = 16


    def __init__(self, parent, ID):
        wx.Window.__init__(self, parent, ID, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        self.SetBackgroundColour("WHITE")
        self.listeners = []
        self.thickness = 1
        self.curLine = []
        self.shape=4
        self.SetColour("Black")
        self.lines = []
        self.redolines=[]
        self.fpos=wx.Point(0,0)
        self.lpos=wx.Point(0,0)
        self.pos = wx.Point(0,0)
        self.MakeMenu()

        self.InitBuffer()

        self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))

        # hook some mouse events
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)

        # the window resize event and idle events for managing the buffer
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        # and the refresh event
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # When the window is destroyed, clean up resources.
        self.Bind(wx.EVT_WINDOW_DESTROY, self.Cleanup)


    def Cleanup(self, evt):
        if hasattr(self, "menu"):
            self.menu.Destroy()
            del self.menu


    def InitBuffer(self,d=None):


        size = self.GetClientSize()
        self.buffer = wx.EmptyBitmap(max(1,size.width), max(1,size.height))
        dc = wx.BufferedDC(d, self.buffer)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        self.DrawLines(dc)
        self.reInitBuffer = False


    def SetColour(self, colour):
        """Set a new colour and make a matching pen"""
        self.colour = colour
        self.pen = wx.Pen(self.colour, self.thickness, wx.SOLID)
        self.Notify()


    def SetThickness(self, num):
        """Set a new line thickness and make a matching pen"""
        self.thickness = num
        self.pen = wx.Pen(self.colour, self.thickness, wx.SOLID)
        self.Notify()


    def GetLinesData(self):
        return self.lines[:]

    def GetBitmapData(self):
        return self.buffer


    def SetLinesData(self, lines):
        self.lines = lines[:]
        self.InitBuffer()
        self.Refresh()


    def MakeMenu(self):
        """Make a menu that can be popped up later"""
        menu = wx.Menu()
        keys = self.menuColours.keys()
        keys.sort()
        for k in keys:
            text = self.menuColours[k]
            menu.Append(k, text, kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU_RANGE, self.OnMenuSetColour, id=100, id2=200)
        self.Bind(wx.EVT_UPDATE_UI_RANGE, self.OnCheckMenuColours, id=100, id2=200)
        menu.Break()

        for x in range(1, self.maxThickness+1):
            menu.Append(x, str(x), kind=wx.ITEM_CHECK)

        self.Bind(wx.EVT_MENU_RANGE, self.OnMenuSetThickness, id=1, id2=self.maxThickness)
        self.Bind(wx.EVT_UPDATE_UI_RANGE, self.OnCheckMenuThickness, id=1, id2=self.maxThickness)
        self.menu = menu


    # These two event handlers are called before the menu is displayed
    # to determine which items should be checked.
    def OnCheckMenuColours(self, event):
        text = self.menuColours[event.GetId()]
        if text == self.colour:
            event.Check(True)
            event.SetText(text.upper())
        else:
            event.Check(False)
            event.SetText(text)

    def OnCheckMenuThickness(self, event):
        if event.GetId() == self.thickness:
            event.Check(True)
        else:
            event.Check(False)


    def OnLeftDown(self, event):
        """called when the left mouse button is pressed"""
        self.InitBuffer()
        if self.shape==0:
           self.pos = event.GetPosition()
           self.InitBuffer()
        elif self.shape==1:
            self.fpos=event.GetPosition()
        elif self.shape==2:
            self.fpos=event.GetPosition()
        elif self.shape==3:
            self.fpos=event.GetPosition()
        elif self.shape==4:
           self.pos = event.GetPosition()
           self.InitBuffer()
        self.CaptureMouse()


    def OnLeftUp(self, event):
        """called when the left mouse button is released"""
        temp=False
        if self.HasCapture():
             if self.shape==0:
                self.curLine.append(event.GetPosition())
                self.lines.append( (self.shape,self.colour, self.thickness, self.curLine) )
                temp=True
                self.InitBuffer()
                self.curLine = []
             elif self.shape==1:
                self.lines.append((self.shape,self.colour,self.thickness,(self.fpos,self.lpos)))
                temp=True
             elif self.shape==2:
                self.lines.append((self.shape,self.colour,self.thickness,(self.fpos,self.lpos)))
                temp=True
             elif self.shape==3:
                self.lines.append((self.shape,self.colour,self.thickness,(self.fpos,self.lpos)))
                temp=True
             elif self.shape==4:
                a=self.curLine[0:len(self.curLine):3]
                a.append(event.GetPosition())
                a.append(event.GetPosition())
                if len(a)>2:
                    self.lines.append((self.shape,self.colour,self.thickness,a))
                    temp=True
                    dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
                    self.reInitBuffer=True
                    self.InitBuffer(dc)
             if temp:
                self.redolines=[]
             self.curLine=[]
             self.reInitBuffer=True
             self.InitBuffer()
             self.ReleaseMouse()
        self.InitBuffer()

    def OnRightUp(self, event):
        """called when the right mouse button is released, will popup the menu"""
        pt = event.GetPosition()
        self.PopupMenu(self.menu, pt)



    def OnMotion(self, event):


        if event.Dragging() and event.LeftIsDown():
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            dc.BeginDrawing()
            dc.SetPen(self.pen)
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            if self.shape==0:
                pos = event.GetPosition()
                coords = (self.pos.x, self.pos.y, pos.x, pos.y)
                self.curLine.append(self.pos)
                dc.DrawLine(*coords)
                self.pos = pos
            elif self.shape==1:
                self.InitBuffer()
                self.lpos=event.GetPosition()
                dc.DrawCircle(self.fpos.x,self.fpos.y,np.linalg.norm(self.fpos-self.lpos))
            elif self.shape==2:
                self.InitBuffer()
                self.lpos=event.GetPosition()
                minp=wx.Point(min(self.lpos.x,self.fpos.x),min(self.lpos.y,self.fpos.y))
                maxp=wx.Point(max(self.lpos.x,self.fpos.x),max(self.lpos.y,self.fpos.y))
                dc.DrawRectangle(minp.x,minp.y,abs(maxp.x-minp.x),abs(maxp.y-minp.y))
            elif self.shape==3:
                self.InitBuffer()
                self.lpos=event.GetPosition()
                dc.DrawLine(self.fpos.x,self.fpos.y,self.lpos.x,self.lpos.y)
            elif self.shape==4:
                pos = event.GetPosition()
                coords = (self.pos.x, self.pos.y, pos.x, pos.y)
                dc.DrawLine(*coords)
                self.curLine.append(self.pos)
                self.pos=pos
            dc.EndDrawing()


    def OnSize(self, event):

        self.reInitBuffer = True


    def LinePop(self):
        if len(self.lines)>=1:
            temp=self.lines.pop()
            self.redolines.append(temp)
            self.reInitBuffer=False
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            self.InitBuffer(dc)
            return True

        else:
            return False

    def LinePush(self):
        if len(self.redolines)>=1:
            temp=self.redolines.pop()
            self.lines.append(temp)
            self.reInitBuffer=False
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            self.InitBuffer(dc)
            return True
        else:
            return False

    def OnIdle(self, event):



        if self.reInitBuffer:
            self.InitBuffer()
            self.Refresh(False)


    def OnPaint(self, event):


        dc = wx.BufferedPaintDC(self, self.buffer)


    def DrawLines(self, dc):



        dc.BeginDrawing()
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        for shape, colour, thickness, line in self.lines:
            pen = wx.Pen(colour, thickness, wx.SOLID)
            dc.SetPen(pen)
            if shape==0:
                for i in range(len(line)-1):
                    coords=(line[i].x,line[i].y,line[i+1].x,line[i+1].y)
                    dc.DrawLine(*coords)
            elif shape==1:
                a,b=line
                dc.DrawCircle(a.x,a.y,np.linalg.norm(a-b))
            elif shape==2:
                a,b=line
                minp=wx.Point(min(b.x,a.x),min(b.y,a.y))
                maxp=wx.Point(max(b.x,a.x),max(b.y,a.y))
                dc.DrawRectangle(minp.x,minp.y,abs(maxp.x-minp.x),abs(maxp.y-minp.y))
            elif shape==3:
                a,b=line
                dc.DrawLine(a.x,a.y,b.x,b.y)
            elif shape==4:
                dc.DrawSpline(line)
                #print "spline"

        dc.EndDrawing()

    def OnMenuSetColour(self, event):
        self.SetColour(self.menuColours[event.GetId()])

    def OnMenuSetThickness(self, event):
        self.SetThickness(event.GetId())


    def AddListener(self, listener):
        self.listeners.append(listener)

    def Notify(self):
        for other in self.listeners:
            other.Update(self.colour, self.thickness)


#----------------------------------------------------------------------

class Frame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "FRAME", size=(800,600),
                         style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        doodle = DoodleWindow(self, -1)

#----------------------------------------------------------------------

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = Frame(None)
    frame.Show(True)
    app.MainLoop()


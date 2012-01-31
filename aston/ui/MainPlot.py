import numpy as np
from aston.ui.Navbar import AstonNavBar
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.path import Path
import matplotlib.patches as patches

class Plotter(object):
    def __init__(self,masterWindow,style='default',scheme='Default'):
        self.masterWindow = masterWindow
        self.style = style
        
        plotArea = masterWindow.ui.plotArea
        
        #create the plotting canvas and its toolbar and add them
        tfig = Figure()
        tfig.set_facecolor('white')
        self.canvas = FigureCanvasQTAgg(tfig)
        self.navbar = AstonNavBar(self.canvas,masterWindow)
        plotArea.addWidget(self.navbar)
        plotArea.addWidget(self.canvas)
    
        self.plt = tfig.add_subplot(111, frameon=False)
        self.plt.xaxis.set_ticks_position('none')
        self.plt.yaxis.set_ticks_position('none')
        
        self.canvas.mpl_connect('button_press_event',self.mousedown)
        self.canvas.mpl_connect('scroll_event',self.mousescroll)

        self.spec_line = None

        self.patches = {}
        
        #These color schemes are modified from ColorBrewer, license as follows:
        #
        #Apache-Style Software License for ColorBrewer software and
        #ColorBrewer Color Schemes
        #
        #Copyright (c) 2002 Cynthia Brewer, Mark Harrower, and
        #The Pennsylvania State University.
        #
        #Licensed under the Apache License, Version 2.0 (the "License")','
        #you may not use this file except in compliance with the License.
        #You may obtain a copy of the License at
        #http://www.apache.org/licenses/LICENSE-2.0
        #
        #Unless required by applicable law or agreed to in writing,
        #software distributed under the License is distributed on an
        #"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
        #either express or implied. See the License for the specific
        #language governing permissions and limitations under the License.
        self._colors = {
            'Default':['#F0F0F0','#8DD3C7','#FFFFB3','#BEBADA','#FB8072','#80B1D3','#FDB462','#B3DE69'],
            'Greys':['#F0F0F0','#D9D9D9','#BDBDBD','#969696','#737373','#525252','#252525','#000000'],
            'Blue-Green':['#E5F5F9','#CCECE6','#99D8C9','#66C2A4','#41AE76','#238B45','#006D2C','#00441B'],
            'Blue-Purple':['#E0ECF4','#BFD3E6','#9EBCDA','#8C96C6','#8C6BB1','#88419D','#810F7C','#4D004B'],
            'Yellow-Red':['#FFEDA0','#FED976','#FEB24C','#FD8D3C','#FC4E2A','#E31A1C','#BD0026','#800026'],
            'Rainbow':['#F0F0F0','#E41A1C','#FF7F00','#FFFF33','#4DAF4A','#377EB8','#984EA3','#A65628'],
            'Spectral':['#F0F0F0','#D53E4F','#FC8D59','#FEE08B','#FFFFBF','#E6F598','#99D594','#3288BD'],
            'Purple-Green':['#F0F0F0','#762A83','#9970AB','#C2A5CF','#E7D4E8','#A6DBA0','#5AAE61','#1B7837']
            }
        self._linestyle = ['-','--',':','-.']
        self.setColorScheme(scheme)

    def setColorScheme(self,scheme='Default'):
        self._color = self._colors[str(scheme)][1:]
        self._peakcolor = self._colors[str(scheme)][0]
        
    def availColors(self):
        return self._colors.keys()

    def availStyles(self):
        return ['Default','Scaled','Stacked','Scaled Stacked','2D']

    def plotData(self,datafiles,peaktable=None,updateBounds=True):
        if not updateBounds:
            bnds = self.plt.get_xlim(),self.plt.get_ylim()

        #plot all of the datafiles
        self.plt.cla()
        if len(datafiles) == 0: return
        if '2d' in self.style:
            #TODO: too slow
            #TODO: choose colormap
            dt = datafiles[0]
            s_mass,e_mass = dt.mz_bounds()
            X,Y = np.meshgrid(dt.time(),np.arange(s_mass,e_mass+1,1))
            Z = np.zeros(X.shape)
            for t in enumerate(dt.time()):
                d = dt.scan(t[1])
                for m,v in zip(d.keys(),d.values()):
                    Z[int(m)-s_mass,t[0]] += v
            self.plt.contourf(X,Y,Z,30,extend='both')#,cmap=self.plt.cm.jet)
            if 'legend' in self.style:
                pass #TODO: add color legend
        else:
            #make up a factor to separate traces by
            if 'stacked' in self.style:
                ftrace = datafiles[0].trace(datafiles[0].getInfo('traces').split(',')[0])
                sc_factor = (max(ftrace)-min(ftrace))/5.

            tnum = 0
            for x in datafiles:
                for y in x.getInfo('traces').split(','):
                    if y == '':
                        continue
                    trace = x.trace(y)
                    if 'scaled' in self.style:
                        trace -= min(trace)
                        trace /= max(trace)
                        trace *= 100
                    if 'stacked' in self.style:
                        trace += tnum * sc_factor
                    c = self._color[int(tnum % 7)]
                    ls = self._linestyle[int(np.floor((tnum % 28)/7))]
                    nm = x.getInfo('name')+' '+y
                    self.plt.plot(x.time(),trace,color=c,ls=ls,lw=1.2,label=nm)
                    tnum += 1

            #add a legend and make it pretty
            if 'legend' in self.style:
                leg = self.plt.legend(frameon=False)
                #leg.get_frame().edgecolor = None
                clrs = [i.get_color() for i in leg.get_lines()]
                for i,j in enumerate(clrs):
                    leg.get_texts()[i].set_color(j)
                for i in leg.get_lines():
                    i.set_linestyle('')


        #update the view bounds in the navbar's history
        if updateBounds:
            self.navbar._views.clear()
            self.navbar._positions.clear()
            self.navbar.push_current()
        else:
            self.plt.set_xlim(bnds[0])
            self.plt.set_ylim(bnds[1])

        #draw peaks
        if peaktable is not None and '2d' not in self.style:
            self.loadCompounds(peaktable.compounds,peaktable.fids)
            self.clearPeaks()

        #draw grid lines
        self.plt.grid(c='black',ls='-',alpha='0.05')

        #update the canvas
        self.canvas.draw()

    def redraw(self):
        self.canvas.draw()

    def drawSpecLine(self,x,color='black',linestyle='-'):
        '''Draw the line that indicates where the spectrum came from.'''
        #try to remove the line from the previous spectrum (if it exists)
        if self.spec_line is not None:
            try:
                self.plt.lines.remove(self.spec_line)
            except ValueError:
                pass #not sure why this happens?
        #draw a new line
        if x is not None:
            self.spec_line = self.plt.axvline(x,color=color,ls=linestyle)
        #redraw the canvas
        self.canvas.draw()
        
    def mousedown(self, event):
        if event.button == 3 and self.navbar.mode != 'align':
            #TODO: make this work for click and drag too
            #get the specral data of the current point
            cur_file = self.masterWindow.ftab_mod.returnSelFile()
            if cur_file is None: return
            if not cur_file.visible: return
            scan = cur_file.scan(event.xdata)
            
            self.masterWindow.specplotter.addSpec(scan)
            self.masterWindow.specplotter.plotSpec()
            self.masterWindow.specplotter.specTime = event.xdata
            
            # draw a line on the main plot for the location
            self.drawSpecLine(event.xdata,linestyle='-')

    def mousescroll(self,event):
        xmin,xmax = self.plt.get_xlim()
        ymin,ymax = self.plt.get_ylim()
        if event.button == 'up': #zoom in
            self.plt.set_xlim(event.xdata-(event.xdata-xmin)/2.,
                                      event.xdata+(xmax-event.xdata)/2.)
            self.plt.set_ylim(event.ydata-(event.ydata-ymin)/2.,
                                      event.ydata+(ymax-event.ydata)/2.)
        elif event.button == 'down': #zoom out
            xmin = event.xdata-2*(event.xdata-xmin),
            xmax = event.xdata+2*(xmax-event.xdata)
            xmin = max(xmin,self.navbar._views.home()[0][0])
            xmax = min(xmax,self.navbar._views.home()[0][1])
            ymin = event.ydata-2*(event.ydata-ymin)
            ymax = event.ydata+2*(ymax-event.ydata)
            ymin = max(ymin,self.navbar._views.home()[0][2])
            ymax = min(ymax,self.navbar._views.home()[0][3])
        self.plt.axis([xmin,xmax,ymin,ymax])
        self.redraw()

    def loadCompounds(self,cmpds,fids):
        if cmpds is None: return
        #generate the patches for peaks in the database
        for i in cmpds:
            for j in i.getPeaks(fids):
                self.addPeak(j)
        self.redraw()

    def clearPeaks(self):
        self.plt.patches = []
        self.redraw()

    def removePeaks(self,pks):
        for pk in pks:
            patch = self.patches[pk.ids[0]]
            self.plt.patches.remove(patch)
        self.redraw()
        
    def addPeak(self,pk):
        self.patches[pk.ids[0]] = patches.PathPatch(Path(pk.data), \
                                  facecolor=self._peakcolor, lw=0)
        self.plt.add_patch(self.patches[pk.ids[0]])

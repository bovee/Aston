class Plotter(object):
    def __init__(self,plt=None,navbar=None,style='default',scheme='default'):
        #TODO: also "style" where style is stacked, 2D, etc.
        #TODO: autoscaled
        self.plt = plt
        self.navbar = navbar
        self.style = style
        self.setColorScheme(scheme)
        
    def setColorScheme(self,scheme='default'):
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
        scheme = str(scheme).lower()
        self._color = {
            'default':['#8DD3C7','#FFFFB3','#BEBADA','#FB8072','#80B1D3','#FDB462','#B3DE69'],
            'greys':['#D9D9D9','#BDBDBD','#969696','#737373','#525252','#252525','#000000'],
            'blue-green':['#CCECE6','#99D8C9','#66C2A4','#41AE76','#238B45','#006D2C','#00441B'],
            'blue-purple':['#BFD3E6','#9EBCDA','#8C96C6','#8C6BB1','#88419D','#810F7C','#4D004B'],
            'yellow-red':['#FED976','#FEB24C','#FD8D3C','#FC4E2A','#E31A1C','#BD0026','#800026'],
            'rainbow':['#E41A1C','#FF7F00','#FFFF33','#4DAF4A','#377EB8','#984EA3','#A65628'],
            'spectral':['#D53E4F','#FC8D59','#FEE08B','#FFFFBF','#E6F598','#99D594','#3288BD'],
            'purple-green':['#762A83','#9970AB','#C2A5CF','#E7D4E8','#A6DBA0','#5AAE61','#1B7837']
            }[scheme]
        self._peakcolor = {
            'default':['#B3E2CD','#FDCDAC','#CBD5E8','#F4CAE4','#E6F5C9','#FFF2AE','#F1E2CC'],
            'greys':7*['#FOFOFO'],
            'blue-green':7*['#E5F5F9'],
            'blue-purple':7*['#E0ECF4'],
            'yellow-red':7*['#FFEDA0'],
            'rainbow':['#FBB4AE','#FED9A6','#FFFFCC','#CCEBC5','#B3CDE3','#DECBE4','#E5D8BD'],
            'spectral':7*['#FOFOFO'], #better choices here
            'purple-green':7*['#FOFOFO'] #better choices here
            }[scheme]
        self._linestyle = ['-','--',':','-.']

    def availColors(self):
        return ['Default','Greys','Blue-Green','Blue-Purple','Yellow-Red', \
                'Rainbow','Spectral','Purple-Green']

    def availStyles(self):
        return ['Default','Scaled','Stacked','Scaled Stacked','2D']

    def plotData(self,datafiles,peaktable=None,updateBounds=True):
        import numpy as np

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
                ftrace = datafiles[0].trace(datafiles[0].info['traces'].split(',')[0])
                sc_factor = (max(ftrace)-min(ftrace))/5.

            tnum = 0
            for x in datafiles:
                for y in x.info['traces'].split(','):
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
                    nm = x.name+' '+y
                    self.plt.plot(x.time(),trace,color=c,linestyle=ls,label=nm)
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
            peaktable.drawPeaks()

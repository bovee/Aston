import numpy as np
        
class SpecPlotter(object):
    def __init__(self,plt=None,cvs=None,style='default'):
        self.plt = plt
        self.canvas = cvs
        self.style = style
        self.scans = {}
        self.scansToDisp = []
        self.scansToLbl = ['']
        self.specTime = None

    def addSpec(self,scan,label=''):
        #save into scans dictionary
        if label is '' and '' in self.scans:
            self.scans['prev'] = self.scans['']
        self.scans[label] = scan
        if label not in self.scansToDisp:
            self.scansToDisp.append(label)
    
    def plotSpec(self):

        #plot it in the area below
        self.plt.cla()
        
        #colors
        clrs = {'':'black','prev':'0.7','lib':'blue'}

        #loop through all of the scans to be displayed
        for scn_nm in self.scansToDisp:
            scn = self.scans[scn_nm]
            try: clr = clrs[scn_nm]
            except: clr = 'black'
            
            #TODO: display UV spectra as continuous lines
            #add the spectral lines (and little points!)
            self.plt.vlines(scn.keys(),[0],scn.values(),color=clr,alpha=0.5)
            self.plt.plot(scn.keys(),scn.values(),',',color=clr)
#            self.plt.set_ylim(bottom=0)

            if scn_nm in self.scansToLbl:
                #go through the top 10% highest ions from highest to lowest
                #always have at least 10 labels, but no more than 50 (arbitrary)
                #if an ion is close to one seen previously, don't display it
                v2lbl = {} #values to label
                plbl = [] #skip labeling these values
                nls = -1*min(max(int(len(scn)/10.0),10),50) #number of labels
                for i in np.array(scn.values()).argsort()[:nls:-1]:
                    mz = scn.keys()[i]
                    if not np.any(np.abs(np.array(plbl)-mz) < 1.5):
                        v2lbl[mz] = scn.values()[i]
                    plbl.append(mz)

                #add peak labels
                for v in v2lbl:
                    self.plt.text(v,v2lbl[v],str(v),ha='center', \
                      va='bottom',rotation=90,size=10,color=clr, \
                      bbox={'boxstyle':'larrow,pad=0.3','fc':clr, \
                            'ec':clr,'lw':1,'alpha':'0.25'})

        #redraw the canvas
        self.canvas.draw()

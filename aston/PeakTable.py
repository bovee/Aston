from PyQt4 import QtCore, QtGui

class PeakTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, database=None, treeView=None, masterWindow=None, selFiles=None, *args): 
        QtCore.QAbstractItemModel.__init__(self, *args)
        self.database = database
        self.fields = ['Name','Type']
        self.masterWindow = masterWindow

        if selFiles is None:
            self.fids = None
            self.compounds = None
        else:
            self.fids = [i.fid[1] for i in selFiles]
            self.compounds = database.getCompounds(self.fids)
        self.patches = {}
        self.drawPeaks()
        
        if treeView is not None:
            self.treeView = treeView
            treeView.setModel(self)

            #set up selections
            self.tab_sel = QtGui.QItemSelectionModel(self,treeView)
            treeView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            treeView.setSelectionModel(self.tab_sel)
            self.connect(self.tab_sel, QtCore.SIGNAL("selectionChanged(const QItemSelection &, const QItemSelection &)"), self.itemSelected)
    
            #set up right-clicking
            treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            treeView.customContextMenuRequested.connect(self.rightClickMenu)
            treeView.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            treeView.header().customContextMenuRequested.connect(self.rightClickMenuHead)

            #prettify
            treeView.resizeColumnToContents(0)
            
    def index(self,row,column,parent):
        if not parent.isValid(): #a compound! (many peaks)
            return self.createIndex(row,column,self.compounds[row])
        else:
        #elif parent.internalPointer() is not None: #a peak!
            peak = parent.internalPointer().getPeaks(self.fids,incSpc=True)[row]
            return self.createIndex(row,column,peak)

    def parent(self,index):
        from .Peak import Compound
        if not index.isValid():
            return QtCore.QModelIndex()
        elif type(index.internalPointer()) is Compound or index.internalPointer() is None:
            return QtCore.QModelIndex()
        else:
            cmpd_id = index.internalPointer().ids[1]
            row = [i.cmpd_id for i in self.compounds].index(cmpd_id)
            return self.createIndex(row,0,self.compounds[row])

    def rowCount(self,parent):
        from .Peak import Compound
        if self.compounds is None: return 0
        if not parent.isValid():
            return len(self.compounds)
        elif type(parent.internalPointer()) is Compound:
            return len(parent.internalPointer().getPeaks(self.fids,incSpc=True))
        else:
            return 0

    def columnCount(self,parent):
        return len(self.fields)

    def data(self,index,role):
        rslt = None
        if not index.isValid():
            rslt = None

        fld = self.fields[index.column()].lower()

        if role != QtCore.Qt.DisplayRole: return None
        if not index.parent().isValid():
            if fld == 'name':
                rslt = index.internalPointer().name
            elif fld == 'd13c':
                rslt = str(index.internalPointer().isotopeValue())
        else:
            if index.internalPointer().ion is None:
                #it's a spectra
                if fld == 'name':
                    #TODO: add support for time() so this works
                    rslt = 'Spectra'# @ '
                    #rslt += format(index.internalPointer().time(),'.3f')
                elif fld == 'type':
                    rslt = index.internalPointer().peaktype
            else:
                #it's a peak
                if fld == 'name':
                    rslt = str(index.internalPointer().ion) + '@'
                    rslt += format(index.internalPointer().time(),'.3f')
                elif fld == 'type':
                    rslt = index.internalPointer().peaktype
                elif fld == 'area':
                    rslt = str(index.internalPointer().area())
                elif fld == 'length':
                    rslt = str(index.internalPointer().length())
                elif fld == 'height':
                    rslt = str(index.internalPointer().height())
                elif fld == 'pwhm':
                    rslt = str(index.internalPointer().length(pwhm=True))
                elif fld == 'time':
                    rslt = str(index.internalPointer().time())
        return rslt

    def headerData(self,col,orientation,role):
        rslt = None
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            rslt = self.fields[col]
        return rslt

    def setData(self,index,data,role):
        data = str(data)
        col = self.fields[index.column()].lower()
        if not index.parent().isValid():
            if col == 'name':
                index.internalPointer().name = data
                self.database.addCompound(index.internalPointer())
        self.dataChanged.emit(index,index)
        return True

    def flags(self, index):
        col = self.fields[index.column()].lower()
        dflags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        if not index.parent().isValid():
            if index.internalPointer().cmpd_id is not None and col == 'name':
                return dflags | QtCore.Qt.ItemIsEditable
            else:
                return dflags
        else:
            return dflags

    def itemSelected(self):
        #TODO: change the selected peak on the graph?
        tab_sel = self.treeView.selectionModel()
        if not tab_sel.currentIndex().isValid: return

        #pk = self.proxyMod.mapToSource(tab_sel.currentIndex()).internalPointer()
        pk = tab_sel.currentIndex().internalPointer()
        if pk is not None:
            if pk.ion is None:
                #it's a spectrum
                self.masterWindow.specplotter.addSpec(pk.verts,'lib')
                self.masterWindow.specplotter.plotSpec()
            else:
                #it's a peak
                pass

    def rightClickMenu(self,point):
        index = self.treeView.indexAt(point)
        menu = QtGui.QMenu(self.treeView)

        if index.isValid():
            if not index.parent().isValid():
                if index.internalPointer().cmpd_id is not None:
                    delAc = menu.addAction('Delete Compound',self._delCompoundFromMenu)
                    delAc.setData(index.internalPointer().cmpd_id)
                    spcAc = menu.addAction('Attach Current Spectrum',self._attSpcFromMenu)
                    spcAc.setData(index.internalPointer().cmpd_id)
            else:
                delAc = menu.addAction('Delete Peak',self._delPeakFromMenu)
                delAc.setData(index.internalPointer().ids[0])
                if index.internalPointer().ion is not None:
                    newAc = menu.addAction('Make New Compound',self._addCompoundFromMenu)
                    newAc.setData(index.internalPointer().ids[0])
        else:
            pass

        if not menu.isEmpty():
            menu.exec_(self.treeView.mapToGlobal(point))

    def rightClickMenuHead(self,point):
        menu = QtGui.QMenu(self.treeView)
        pos_flds = ['Type','Area','Height','Length','PWHM','Time','d13C']
        for fld in pos_flds:
            ac = menu.addAction(fld,self.rightClickMenuHeadHandler)
            ac.setCheckable(True)
            if fld in self.fields: ac.setChecked(True)
        if not menu.isEmpty(): menu.exec_(self.treeView.mapToGlobal(point))
    
    def rightClickMenuHeadHandler(self):
        fld = str(self.sender().text())
        if fld == 'Name': return
        self.beginResetModel()
        if fld in self.fields:
            self.fields.remove(fld)
        else:
            self.treeView.resizeColumnToContents(len(self.fields)-1)
            self.fields.append(fld)
        self.endResetModel()

    def _delCompoundFromMenu(self):
        cmpd_id = self.sender().data()
        self.delCompound(cmpd_id)

    def _attSpcFromMenu(self):
        cmpd_id = self.sender().data()
        dt = self.masterWindow.ftab_mod.returnSelFile()
        #FIXME: this won't match the current spectra if the user has selected something else
        for cmpd in self.compounds:
            if cmpd.cmpd_id == cmpd_id:
                #TODO: get the actual spectra
                verts = [] #spectrum
                #TODO: make the peak type MS or UV?
                pk = Peak.Peak(verts,None,'spectra')
                pk.ids[2] = dt.fid[1]
                cmpd.addPeak(pk)

    def _addCompoundFromMenu(self):
        pk_id = self.sender().data()
        pk = None
        self.beginResetModel()
        for i in self.compounds:
            for j in i.getPeaks(self.fids):
                if j.ids[0] == pk_id:
                    i.peaks.remove(j)
                    pk = j
                    break
        if pk is None: return
        self.addCompoundWithPeak(pk,'New Compound')
        self.endResetModel()
    
    def _delPeakFromMenu(self):
        pk_id = self.sender().data()
        pk = None
        for i in self.compounds:
            for j in i.peaks:
                if j.ids[0] == pk_id:
                    pk = j
                    break
        if pk is None: return
        self.delPeak(pk)        

    # The following functions are not overriden, but deal
    # with stuff in the peaks database so they're here.

    def addPatchToCanvas(self,pk):
        from matplotlib.path import Path
        import matplotlib.patches as patches
        self.patches[pk.ids[0]] = patches.PathPatch(Path(pk.verts),facecolor='orange',lw=0)
        self.masterWindow.tplot.add_patch(self.patches[pk.ids[0]])

    def findPeak(self,x,y):
        lst = []
        for i in self.compounds:
            for j in i.getPeaks(self.fids):
                if j.contains(x,y):
                    lst.append(j)
        return lst

    def addCompoundWithPeak(self,pk,name):
        from .Peak import Compound
        new_cmpd = Compound(name,self.database)
        self.database.addCompound(new_cmpd)
        new_cmpd.addPeak(pk)
        self.compounds = self.database.getCompounds(self.fids)

    def delCompound(self,cmpd_id):
        #delete all the patchs assigned to pks belonging to this cmpd
        #TODO: remove this code if peaks are moved to 'Unassigned'
        for cmpd in self.compounds:
            if cmpd.cmpd_id == cmpd_id:
                for peak in cmpd.peaks:
                    if peak.ion is not None:
                        patch = self.patches[peak.ids[0]]
                        self.masterWindow.tplot.patches.remove(patch)
                self.masterWindow.tcanvas.draw()
                break
            
        self.beginResetModel()
        self.database.delCompound(cmpd_id)
        self.compounds = self.database.getCompounds(self.fids)
        self.endResetModel()

    def delPeak(self,peak):
        for cmpd in self.compounds:
            if peak in cmpd.getPeaks(self.fids,incSpc=True):
                if peak.ion is not None:
                    patch = self.patches[peak.ids[0]]
                    self.masterWindow.tplot.patches.remove(patch)
                    self.masterWindow.tcanvas.draw()
                self.beginResetModel()
                if len(cmpd.getPeaks(self.fids)) == 1 and cmpd.cmpd_id is not None:
                    self.database.delCompound(cmpd.cmpd_id)
                    self.compounds = self.database.getCompounds(self.fids)
                else:
                    cmpd.delPeak(peak)
                self.endResetModel()
                break

    def addPeaks(self,pks):
        self.beginResetModel()
        for pk in pks:
            self.compounds[0].addPeak(pk)
            if pk.ion is not None:
                self.addPatchToCanvas(pk)
        self.endResetModel()
        self.masterWindow.tcanvas.draw()

    def drawPeaks(self):
        if self.compounds is None: return
        #generate the patches for peaks in the database
        for i in self.compounds:
            for j in i.getPeaks(self.fids):
                self.addPatchToCanvas(j)
        self.masterWindow.tcanvas.draw()

    def clearPatches(self):
        self.masterWindow.tplot.patches = []
        self.masterWindow.tcanvas.draw()

#No good place to put automatic integration functions, so
#they're here for now.

def waveletIntegrate(ptab,dt,ion=None):
    #TODO: make this an integration option
    import numpy as np, scipy.ndimage as nd
    x = dt.trace(ion)
    t = dt.time()

    nstep = 20 # number of frequencies to analyse at
    z = np.zeros((nstep,len(x)))

    # fxn to calculate window size based on step
    f = lambda i: int((len(x)**(1./(nstep+2.)))**i) #22*(x+1)
    
    for i in xrange(0,nstep):
        # how long should the wavelet be?
        hat_len = f(i)
        # determine the support of the mexican hat
        rng = np.linspace(-5,5,hat_len)
        # create an array with a mexican hat
        hat =  1/np.sqrt(hat_len) * (1 - rng**2) * np.exp(-rng**2 / 2)
        # convolve the wavelet with the signal at this scale levelax2.
        z[i] = np.convolve(x,hat,'same')

    # plot the wavelet coefficients
    #from matplotlib import cm
    #xs,ys = np.meshgrid(self.data.time(),np.linspace(self.max_bounds[2],self.max_bounds[3],nstep))
    #self.tplot.contourf(xs,ys,z,300,cmap=cm.binary)
    #self.tcanvas.draw()

    # create an True-False array of the local maxima
    mx = (z == nd.maximum_filter(z,size=(3,17),mode='nearest')) & (z > 100)
    # get the indices of the local maxima
    inds = np.array([i[mx] for i in np.indices(mx.shape)]).T

    from matplotlib.path import Path
    import matplotlib.patches as patches
    for i in inds:
        #get peak time, width and "area"
        #pk_t, pk_w, pk_a = t[i[1]], f(i[0]), z[i[0],i[1]]
        #print pk_t, pk_w, pk_a
        #try:
        rng = np.linspace(t[int(i[1]-i[0]/2.)], t[int(i[1]+i[0]/2.)], i[0])
        verts = z[i[0],i[1]]/np.sqrt(2*np.pi) * np.exp(np.linspace(-5.,5.,i[0])**2/-2.)
        verts += x[i[1]] - verts[int(i[0]/2)]
        y = patches.PathPatch(Path(zip(rng,verts)),facecolor='red',lw=0)
        ptab.masterWindow.tplot.add_patch(y)
        #except:
        pass

def statSlopeIntegrate(ptab,dt,ion=None):
    import numpy as np
    from .Peak import Peak
    t = dt.time()
    x = dt.trace(ion)
    pks = []

    dx = np.gradient(x)
    dx2 = np.gradient(dx)

    adx = np.average(dx)
    adx2 = np.average(dx2)
    l_i = -2

    #old loop checked for concavity too; prob. not necessary
    #for i in np.arange(len(t))[dx>adx+np.std(dx[abs(dx2)<adx2+np.std(dx2)])]:

    #loop through all of the points that have a slope 
    #outside of one std. dev. from average
    for i in np.arange(len(t))[dx>adx+np.std(dx)]:
        if i - l_i == 1:
            l_i = i
            continue

        #track backwards to find where this peak started
        pt1 = ()
        for j in range(i-1,0,-1):
            if dx[j] < adx or dx2[j] < adx2:
                pt1 = (t[j],x[j])
                break

        #track forwards to find where it ends
        pt2 = ()
        neg = 0
        for j in range(i,len(t)):
            if dx[j] < adx: neg += 1
            if neg > 3 and dx[j] > adx: # and x[j]<ax:
                pt2 = (t[j],x[j])
                break

        #create a peak and add it to the peak list
        if pt1 != () and pt2 != ():
            verts = [pt1]
            verts += zip(dt.time(pt1[0],pt2[0]),dt.trace(ion,pt1[0],pt2[0]))
            verts += [pt2]
            pk = Peak(verts,ion,'StatSlope')
            pk.ids[2] = dt.fid[1]
            pks.append(pk)
        l_i = i
    return pks

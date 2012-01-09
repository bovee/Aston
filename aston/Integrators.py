import numpy as np
import scipy.ndimage as nd
from aston.Features import Peak

#TODO: remove these imports
from matplotlib.path import Path
import matplotlib.patches as patches

def waveletIntegrate(ptab,dt,ion=None):
    #TODO: make this an integration option
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

def statSlopeIntegrate(dt,ion=None):
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
            pk = Peak(verts,None,ion,'StatSlope')
            pk.ids[2] = dt.fid[1]
            pks.append(pk)
        l_i = i
    return pks

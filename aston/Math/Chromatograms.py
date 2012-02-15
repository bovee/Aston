import numpy as np
 
def fft(ic):
    #FIXME: "time" of FFT axis doesn't match time of ic axis
    oc = np.abs(np.fft.fftshift(np.fft.fft(ic))) / len(ic)
#elif fxn == 'ifft':
#    ic = np.fft.ifft(np.fft.fftshift(ic * len(ic)))# / len(ic)
    
def noisefilter(ic,bandwidth):
    #adapted from http://glowingpython.blogspot.com/
    #2011/08/fourier-transforms-and-image-filtering.html
    I = np.fft.fftshift(np.fft.fft(ic)) # entering to frequency domain
    # fftshift moves zero-frequency component to the center of the array
    P = np.zeros(len(I), dtype=complex)
    c1 = len(I)/2 # spectrum center
    r = float(bandwidth) #percent of signal to save
    r = int((r*len(I))/2) #convert to coverage of the array
    for i in range(c1-r, c1+r):
        P[i] = I[i] # frequency cutting
    oc = np.real(np.fft.ifft(np.fft.ifftshift(P)))
    
def abs(ic):
    oc = np.abs(ic)
    
def sin(ic):
    oc = np.sin(ic)
    
def cos(ic):
    oc = np.cos(ic)
    
def tan(ic):
    oc = np.tan(ic)

def d(ic):
    return derivative(ic)

def derivative(ic):
    #FIXME: not adjusted for time at all
    return np.gradient(ic)
    
def base(ic):
    #INSPIRED by Algorithm A12 from Zupan
    #5 point pre-smoothing
    sc = np.convolve(np.ones(5) / 5.0, ic, mode='same')
    #get local minima
    mn = np.arange(len(ic))[np.r_[True,((sc < np.roll(sc, 1)) &
      (sc < np.roll(sc, -1)))[1:-1], True]]
    #don't allow baseline to have a slope greater than
    #10x less than the steepest peak
    max_slope = np.max(np.gradient(ic))/10.0
    slope = max_slope
    pi = 0 #previous index
    oc = np.zeros(len(ic))
    for i in range(1, len(mn)):
        if slope < (ic[mn[i]]-ic[mn[pi]]) / (mn[i]-mn[pi]) and \
          slope < max_slope:
            #add trend
            oc[mn[pi]:mn[i-1]] = \
              np.linspace(ic[mn[pi]],ic[mn[i-1]],mn[i-1]-mn[pi])
            pi = i -1
        slope = (ic[mn[i]]-ic[mn[pi]])/(mn[i]-mn[pi])
    print(mn[pi], mn[-1])
    oc[mn[pi]:mn[-1]] = \
      np.linspace(ic[mn[pi]],ic[mn[-1]],mn[-1]-mn[pi])
    oc[-1] = oc[-2] #FIXME: there's definitely a bug in here somewhere
    
def movingaverage(ic, window):
    pass

def savitzkygolay(ic, window, order):
    pass
elif (fxn == 'movingaverage' and len(args) == 1) or \
  (fxn == 'savitskygolay' and len(args) == 2):
    if fxn == 'movingaverage':
        x = int(args[0])
        half_wind = (x-1) // 2
        m = np.ones(x) / x
    elif fxn == 'savitskygolay':
        # adapted from http://www.scipy.org/Cookbook/SavitzkyGolay
        half_wind = (int(args[0]) -1) // 2
        order_range = range(int(args[1])+1)
        # precompute coefficients
        b = [[k**i for i in order_range] \
             for k in range(-half_wind, half_wind+1)]
        m = np.linalg.pinv(b)
        m = m[0]
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = ic[0] - np.abs(ic[1:half_wind+1][::-1] - ic[0])
    lastvals = ic[-1] + np.abs(ic[-half_wind-1:-1][::-1] - ic[-1])
    y = np.concatenate((firstvals, ic, lastvals))
    oc = np.convolve(m, y, mode='valid')
else:
    oc = ic
return oc

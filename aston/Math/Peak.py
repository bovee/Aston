import numpy as np

def area(data):
    csum = 0
    x, y = data[-1,:]
    for i in data:
        csum += i[0] * y - i[1] * x
        x, y = i
    return abs(csum / 2.)

def length(data, pwhm=False):
    if pwhm:
        #TODO: better way to pick these points
        pt1,pt2 = data[0], data[-1]

        m = (pt2[1]-pt1[1]) / (pt2[0]-pt1[0])
        avs = np.array([(pt[0],(pt[1] - m*(pt[0]-pt1[0]) - pt1[1])) for pt in data])

        #calculate the height of half-max
        half_y = max(avs[:,1]) / 2.0
        lw_x,hi_x = float('nan'), float('nan')
        #loop through all of the line segments
        for i in range(len(avs)-1):
            #does this line segment intersect half-max?
            if (avs[i,1]<half_y and avs[i+1,1]>half_y) or (avs[i,1]>half_y and avs[i+1,1]<half_y):
                m = (avs[i+1,1]-avs[i,1]) / (avs[i+1,0]-avs[i,0])
                b = (avs[i+1,0]*avs[i,1] - avs[i,0]*avs[i+1,1]) / (avs[i+1,0]-avs[i,0])
                if np.isnan(lw_x) and np.isnan(hi_x):
                    lw_x,hi_x = (half_y-b)/m, (half_y-b)/m
                else:
                    lw_x,hi_x = min((half_y-b)/m,lw_x), max((half_y-b)/m,hi_x)
        return hi_x - lw_x
    else:
        data = np.array(data)
        return data[:,0].max() - data[:,0].min()

def height(data):
    data = np.array(data)
    return data[:,1].max() - data[:,1].min()

def time(data):
    if data[1,0] < data[:,0].max():
        return data[data[:,1].argmax(),0]
    else: # inverted peak
        return data[data[:,1].argmin(),0]

def contains(data,x,y):
    #from: http://www.ariel.com.au/a/python-point-int-poly.html
    n = len(data)
    inside = False

    p1x, p1y = data[0]
    for i in range(n+1):
        p2x, p2y = data[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

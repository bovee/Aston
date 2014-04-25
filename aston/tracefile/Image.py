from aston.tracefile.TraceFile import TraceFile


#class PNGImage(TraceFile):
class PNGImage(object):
    #TODO: should actually create a helper file for each image
    # that has orientation (top-bottom/left-right), how to weight
    # color channels, and lane widths. use this helper file instead
    # of the original image
    ext = 'PNG'
    mgc = '8950'

    @property
    def data(self):
        pass

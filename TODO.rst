0.7 Features
************

*


0.7 Checklist
*************
* plot all 1d traces in same axes, each 2d gets its own axes (but x-axis is linked?)
* allow scaling/stacking of 1d traces
* remove "extras", "graph style" options from graph menu
* axes labels? (e.g. R.T. (min), etc)
* make all columns display in tables properly
* save AIA/CDF, mzML & mzXML
* RAW file support
  - look at linking to unfinnigan? (https://code.google.com/p/unfinnigan/)
* Bruker file formats
* Waters file formats
* Chemstation A fraction collection
* Chemstation B+ FIA
* MSMS support
  - Agilent MSMS Peak file format
  - Bruker MSMS spectra
* work on spectral display
* compound libraries
* inner product/neutral loss chromatograms


0.8 Checklist
*************

* Agilent .REG scraping
  - method parameters
* autoalign chromatograms
* baseline detection
* smarter peak editing?
  - peak groups
  - adjustable peaks (little selectors on each end of "baseline")
  - allow user-selected peaks to be re-interpreted &
    coelution spots to be found
* spectra from Agilent MS SIM method (e.g. CM1292) have a "0" mz
  that may be erroneous and should be removed?
* fix color scaling as more chromatograms added: hard to keep track
* put retention time on extracted spectra
* buttons for spectral navigation?
* xcms interface


0.9 Checklist
*************

* MSMS support
  - tune MSMS file format performance (rewrites in C?)
  - spectral range display (as average) for Agilent MSMS
  - MSMS points on graph / MSMS data display
* Method Database
  - allow calibration curves to be saved for compounds
  - method editor?
  - setting to allow run info to be loaded from method DB
* remote database support
* have multiple plots and allow user to choose which plot each trace goes on?
  - have datafile return units associated with trace types to allow for multiple y axes
* allow fake datafiles to be generated and added to the library
  for chromatography models
* display x axes in seconds (or hours or scans)
  (http://stackoverflow.com/questions/9451395/customize-x-axis-in-matplotlib)
* help manual / tutorials
* package example data with aston (for tests / quality control)
* write unit tests


Indefinite
**********
* MWD import: check changes in "peak width", e.g. sampling rate (0x212 or 0x214?)
* package size on Macs
* setup/disttools? need better versioning
* use hashes of data instead of filenames to match data to database entries
  - but how to handle duplicate files?
* refactor code to remove references to "ions"; should be mz or wavelength?
* 2D display of multiple chromatograms at once (i.e. "color bars" of TICs of multiple files vertically stacked)
* make TimeSeries either have a string descriptor for ions *or* an array of numbers
* TraceFiles should be able to match filenames using regex

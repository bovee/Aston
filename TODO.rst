0.7 Checklist
*************

* mzML & mzXML file support
* save AIA/CDF, mzML & mzXML
* RAW file support
  - look at linking to unfinnigan? (https://code.google.com/p/unfinnigan/)
* Chemstation B+ REG files
* Agilent .REG scraping
  - method parameters
  - fraction collection
* remote database support
* autoalign chromatograms
* baseline detection
* smarter peak editing?
  - peak groups
  - adjustable peaks (little selectors on each end of "baseline")
  - highlight selected (in peak table) peak on graph
  - allow user-selected peaks to be re-interpreted &
    coelution spots to be found
* extract spectra from SIM method file properly (e.g. CM1292)
* ion ranges (34:45) are weird?
* make aston not freak out if datafile is not found?


0.8 Checklist
*************

* MSMS support
  - tune MSMS file format performance (rewrites in C?)
  - Agilent MSMS Peak file format
  - spectral range display (as average) for Agilent MSMS
  - Bruker MSMS spectra
  - MSMS points on graph / MSMS data display
* Method Database
  - allow calibration curves to be saved for compounds
  - method editor?
  - setting to allow run info to be loaded from method DB
* have multiple plots and allow user to choose which plot each trace goes on?
  - have datafile return units associated with trace types to allow for multiple y axes
* allow fake datafiles to be generated and added to the library
  that model chromatography
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

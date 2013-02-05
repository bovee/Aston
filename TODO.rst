0.6 Checklist
*************

* mzML, & mzXML file support
* save AIA/CDF, mzML & mzXML
* RAW file support
* MSMS support
  - Agilent MSMS Peak file format
  - spectral range display (as average) for Agilent MSMS
  - Bruker MSMS spectra
  - MSMS points on graph / MSMS data display
* Chemstation B+ REG files
* Agilent .REG scraping
  - method parameters
  - fraction collection
* compound database
  - hashing code for compounds? numerical match score between spectra?
* remote database support
* autoalign chromatograms
* rewrite database code to use context manager for "lazy" system
* baseline detection (as a trace type?)
* smarter peak editing?
  - adjustable peaks (little selectors on each end of "baseline")
  - highlight selected (in peak table) peak on graph
* allow user-selected peaks to be re-interpreted &
  coelution spots to be found
* periodic integration (to replace old "split peaks" code)


0.7 Checklist
*************

* optimization
  - seperate thread for database updating
  - tune MSMS file format performance (rewrites in C?)
* Method Database
  - allow calibration curves to be saved for compounds
  - method editor?
  - setting to allow run info to be loaded from method DB
* have multiple plots and allow user to choose which plot each trace goes on?
  - have datafile return units associated with trace types to allow for multiple y axes
* display x axes in seconds (or hours or scans)
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

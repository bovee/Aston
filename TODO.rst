0.5 Checklist
*************

* mzML, & mzXML file support
* save AIA/CDF, mzML & mzXML
* display extras on graph
  - fraction collection windows
* applications for "time window" alignment
  - integrate all traces as first (isotopic mode)
  - integrate by fraction collection windows/ref gas
* finish trace selector dialog
  - delete items from ion list
  - low-high error checking for ranges, make sure ions are numbers, etc
* better spectra display
  - display range as average for Agilent MSMS
  - allow navigation around window

0.6 Checklist
*************

* RAW file support
* MSMS support
  - Agilent MSMS Peak file format
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


0.7 Checklist
*************

* optimization
  - seperate thread for database updating
  - tune MSMS file format performance (rewrites in C?)
* Method Database
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

0.4 Checklist
*************

* fix CSV export of chromatograms and spectra
* open mzML & mzXML
* save mzML & mzXML
* allow selection of spectra ranges (by averaging)
* shift-click save spectra to current file

0.5 Checklist
*************

* icon for Aston
* AIA/CDF and RAW file support
* Agilent .REG scraping
  - fraction collection display
  - pressure/flow rate/temp
* MSMS points on graph / MSMS data display
* Agilent MSMS Peak file format
* Bruker MSMS spectra
* Method Database
* setting to allow run info to be loaded from method DB
* wavelet integration
* finish trace selector dialog
  - delete items from ion list
  - low-high error checking for ranges, make sure ions are numbers, etc
* make sure all dates are in consistent format (in file table)

0.6 Checklist
*************

* method editor?
* compound database
  - hashing code for compounds? numerical match score between spectra?
* remote database support
* autoalign chromatograms
* noise removal
* baseline detection (as a trace type?)
* smarter peak editing?
  - adjustable peaks (little selectors on each end of "baseline")
  - highlight selected (in peak table) peak on graph
* help manual / tutorials
* package example data with aston (for tests / quality control)
* write unit tests


0.7 Checklist
*************

* optimization
  - seperate thread for database updating
  - tune MSMS file format performance (rewrites in C?)
* have multiple plots and allow user to choose which plot each trace goes on?
* display x axes in seconds (or hours)


Indefinite
**********
* MWD import: check changes in "peak width", e.g. sampling rate (0x212 or 0x214?)
* package size on Macs
* setup/disttools? need better versioning
* use hashes of data instead of filenames to match data to database entries
  - but how to handle duplicate files?
* have datafile return units associated with trace types to allow for multiple y axes

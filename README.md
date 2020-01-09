# SHETran Results Viewer

## Features
- Visualise SHETran model outputs based on the library file
- Plots and maps specific elements or time steps
- Compare model results with each other or CSV time series
- Export results from multiple models to a CSV file
- Allows any EPSG spatial projection 
- Converts time values to dates based on start date in library file
- Drag and drop both CSVs and library files to add
- Zoom in on the plot at the current time step
- Customize the names of models
- Adds a water table elevation variable based on phreatic depth values

## Installation
 
Download either the standalone exe or zip file from the latest release 
(https://github.com/nclwater/shetran-results-viewer/releases/latest). 
The standalone exe is slower to start but more compact.
If using the zip file, extract it and then run the exe file from the extracted directory.

## Usage

### Library File Format
The XML file does not need to be valid. 
The only required elements are the start date, catchment name and DEM mean file name:

```xml
<ShetranInput>
    <CatchmentName>Example_Catchment</CatchmentName>
    <DEMMeanFileName>Example_DEM.txt</DEMManFileName>
    <StartDay>01</StartDay>
    <StartMonth>01</StartMonth>
    <StartYear>2019</StartYear>
</ShetranInput>
```

The DEM and HDF files must be in the same directory as the library file.

#### Spatial Projection
The spatial projection can be specified in the library file like this:

```xml
<SRID>EPSG:27700</SRID>
```

### Time Series
To add time series from a CSV file, it should be similar to:

```csv
times, values
2019-12-31T09:00:00, 1.234
```

Column names are ignored. Times are assumed to be in the first column and values in the second.

The CSV data only persists for as long as you have the current element selected. 


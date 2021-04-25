# purpleair-data-tools - pasc.py
Tool for combining and optionally summaizing PurpleAir PAII historical data files.  
Additional functionality allows for the inclusion of regulatory station and wind data.  
Outputs to several different file formats. csv, Excel and formatted for RETIGO.  

Python installation requirements
   Requires Python 3.6.8 or higher.

   Install the following Python packages:
    If python on your system aliases to python3
      (python -m pip install [package], e.g., python -m pip install pandas)

    If python on your system aliases to python2.x
      (python3 -m pip install [package], e.g., python3 -m pip install pandas)

   ## Required Packages:
   * pandas
   * matplotlib
   * prettytable
   * xlsxwriter
   * tqdm

    Note: on Linux systems "sudo apt-get install python-matplotlib" may be
    required in lieu of "python -m pip install matplotlib".

## Basic instructions for installation and use:
   1. Copy pasc.py, pasc_ref_stations.csv and config.py file to a folder on your computer.
   2. Edit the pasc_ref_stations.csv file as needed for the regulatory stations you want to use if any.
   3. Edit the config.py file with details about your file storage locations.
   4. Download historical primary and secondary PurpleAir sensor data for both the A & B channels to a folder on your computer.
     1. See the pa-get-data git repo for a tool that facilitates downloading PurpleAir historical data.
   5. Download reference data with a one day later range than the Purpleair
       data to account for 8-hour time shift.
   6. Optionally download AQMD regulatory site reference data to the same folder
    as the PurpleAir sensor data. This is required to use the -r or -w options.
       See below for details on specific file naming conventions.
   7. Optionally download darksky wind data to the same folder as the PurpleAir
    sensor data. This is required to use the -k option.
       See below for detials on specific file naming conventions.
   8. Run python pasc.py from the command line with any optional flags and arguments as defined below.

   Selected combined and summarized files will be created in the same folder as the historical sensor data files.


## Description of operation:
    Iterates over all PurpleAir sensor csv files located in a user specified data directory.
      and combines them into a files in various formats with re-ordered columns, UTC datetime conversion and sensor LAT/LON coordinates.

      AQS / ARB Reference sensor and/or darksky wind data may also be optionally included.
         Note reference data functionality is a work in progress and limited to only specific stations at this time (Lake Elsinore and Norco) and only
            one station at a time.

    The combined data is resampled by averaging the readings over a specified interval and saved as new summarized Excel and/or csv file(s) as selected
      by the user (see command line arguments below).

    The PM 2.5 AQI is calculated and included in the output files in the Ipm25 column.

 The available output file formats are described below:

    combined_full.csv. This file is optionaly created using the -f flag and combines the csv files into one file, adds a column with the Sensor Name
       and columns for Lat / Lon.
 
    combined_summarized_csv.csv. This file is optionally created using the -o argument. Data are summarized over the specified interval, Column order
       is changed, the timestamp is converted to Pacific Time (Standard or Daylight Savings adjustment is automatic based on the date of the timestamp).

    combined_summarized_xl.xlsx. This file is optionally created using the -o argument. Similar to combined_summarized.csv but in Microsoft XLSX format. 
       Top row is frozen, column names are bolded. Column widths and cell formats are set. The code in the Excel section may be extended using Pandas 
       to perform any number of analyses, summarization, grouping, calculated fields, PivotTable like operations, plotting (using XlsxWriter) etc.

    combined_summarized_retigo.csv. This file is optionally created using the -o argument. Data are summarized over the specified interval. Timestamp is
    converted to the required UTC/ISO 8601 international standard for the defined local time zone, columns are reordered and renamed as needed for RETIGO input.

    XXXX_station_merged.csv where XXXX is the prefix of the AQS / ARB reference station obtained from the csv filename. 
       This file is optionally created by using the "-r" or -"w" flags.
       This file contains merged data from reference station files. 
       IMPORTANT See the combine_reference() function comments for more details on how to properly name the reference files prior to using this option.


 Detailed instructions for use:

 Run from command line 

 Usage:  python pasc.py [-d <data directory>] [-r] [-w] [-k] [-s <summary interval>] [-l] [-o <output <type(s)>] [-p] [-y <yaxis scale (integer)>] [-f]

   -d argument enter existing "data directory" without path. e.g. "data5".
   -r flag include AQS / ARB station reference data.
   -w flag include AQS / ARB station reference data and include wind data in summary output.
   -k flag include darksky wind data in summary output.
   -s argument summary interval. e.g. "15min" or "1H" etc. 
         valid values are 'W' (week), 'D" (day), "H" (hour), "min" or "T" (min), "S" (second).
   -l flag display a list of reference stations. This flag supersedes other arguments and flags.
   -o argument output type e.g. "csv", "xl", "retigo", "all", "none", "xl retigo", "csv xl".
   -p flag generate a simple plot of PM2.5 vs time. Close the plot to end the script.
   -y argument integer set yaxis range of the plot. e.g. -y 75
   -f flag output the combined sensor data files to combined_full.csv

   Example: "python pasc.py -d Data1 -s 1H -o retigo". Combines files in Data1, summarizes over 1-hour intervals and outputs a RETIGO csv file.
   Example: "python pasc.py -d Data1 -s 1H -o retigo -p -y 75" same as above and then outputs a plot with a y-axis range of 75.

   -or-: "python pasc.py" without one or more arguments will use the defaults defined in the argument defaults section.
   use with -h or --help for help.

##  Notes for using reference files
     Combines data from downloaded AQMD regulatory stations and station coordinate information into a single file
     Looks for specifically named reference data csv's in the data folder, combines them and appends them to the combined primary data csv file
     IMPORTANT Ensure the reference data files are named per below and included in the same directory as the PA Primary csv files.
        Reference csv files must be named as follows:
           prefix for the sensor you want followed by _REF_ followed by the sensor type in lowercase.
           for appropriate prefixes to use (i.e., "LE" or "NORCO") look in pasc_ref_stations.csv. This is kludgy, it's a work in progress.
           Sensor types:
              25, wd, ws (correspond to PM2.5, Wind Direction and Wind Speed)
           e.g. LE_REF_25.csv or NORCO_REF_wd.csv
     Reference station coordinate and other information is included in the file "pasc_ref_stations.csv" which must be stored 
        in the same folder as pasc.py. Modify "pasc_ref_stations.csv as required to add reference stations
     Timestamps in the merged file are converted to UTC to be consistent with the combined Primary csv timestamps.
     Reference station historical data from SCAQMD regulatory sites are not daylight savings corrected and are always in PST (UTC -8 hours). 
        This is accounted for when converting to UTC (fixed 8-hour offset).

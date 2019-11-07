pasc.py
Prepares PurpleAir sensor historical data for further analysis.
   (csv files downloaded from www.purpleair.com/sensorlist).

Python installation requirements
   This code works with Python 2.7.16 or Python 3.6.8 on Windows 10 or Linux.

   Install the following Python packages:
      (python -m pip install [package], e.g., python -m pip install pandas)
                                   -or-
      (python3 -m pip install [package], e.g., python3 -m pip install pandas)

   Required Packages:
      pandas
      matplotlib
      prettytable
      xlsxwriter

    Note: on Linux systems "sudo apt-get install python-matplotlib" may be
    required in lieu of "python -m pip install matplotlib".

 Basic instructions for installation and use:
    Copy this file and the pasc_ref_stations.csv file to a folder on your computer.
    Download historical PurpleAir sensor data to a folder on your computer.
    Download reference data with a one day longer range than Purpleair
       data to account for 8-hour time shift.
    Optionally download AQMD regulatory site reference data to the same folder
    as the PurpleAir sensor data. This is required to use the -r or -w options.
       See below for details on specific file naming conventions.
    Optionally download darksky wind data to the same folder as the PurpleAir
    sensor data. This is required to use the -k option.
       See below for detials on specific file naming conventions.
    Change the variables in the USER VARIABLES section to set the path to the parent of the folder you uploaded to and change any other user variables.
    Run python pasc.py from the command line with any optional flags and arguments as defined below.
    Selected combined and summarized files will be created in the same folder as the historical sensor data files.


 Description of operation:
    Iterates over all PurpleAir "primary" sensor csv files located in a user specified data directory.
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


 FOR USER: Edit ---USER VARIABLES--- section for variables that must be changed prior to running the program.


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


 Todo: General optimization
 Todo: Automated data validation, data integrity checks and additional specific error handling.
 Todo: Generally improve how reference data is handled. Eliminate the need to name reference data files so specifically if possible.
 Todo: Combine reference data from multiple sources (e.g., weather underground) and localize to nearest sensor(s)
 Todo: Maybe create separate summary output files when incorporating wind reference. This would allow summary and wind reference to have different intervals
 Todo: Automate or generalize dataframe column names based on availability of reference data (e.g., temperature file missing)
 Todo: Code relies on assumptions about underlying data format. e.g., if the PurpleAir format changes, this breaks. Needs improvement.
 Todo: Reduce / eliminate need to create / drop / recreate dataframe indices just for the sake of timezone conversions.
 Todo: Add plot date range argument
 Todo: Convert to Python class
 Todo: Add regional grouping functionality?
 Todo: Additional Pandas analysis, Pandas matplotlib Plots and/or Excel Charts (via XlsxWriter).
 Todo: Auto archive previous output files?
 Todo: Set preferences such as data path, time zone etc from command line and store in config file?
 Todo: Currently dropping various rows with nulls in retigo output, is there a better way?
 Todo: Would be nice if the -s interval check in summarize() could be done earlier.
 Todo: Investigate using HDF5 in-lieu of csv for combined_full
 Todo: get_arguments() add argparse choices to -s
 Todo: Test use of -w and -k arguments at the same time and correct any issues
 Todo: Handle errors when -k flag and no darksy file

 Changes:
    20190805: Changed "\\" to os.path.sep. Allows use on Linux and Windows without code modification.
              Code now runs on Linux.
    20190805: get_reference() fixed an issue where underscore (_) in path would break parsing (now using basename instead of filename).
    20190810: Modified combine_primary() to use Pandas in-lieu of the CSV module. Significantly reduces csv read/write operations.
              added -f flag to optionally write combined sensor data to combined_full.csv. Changed default behavior to not write combined data.
    20190817: Filter reference and darksky data to match data range of primary data. Prevents null wind values in output files.
    20190818: Added status_message() function.
    20190901: Now runs on both Python 2.7.16 and Python 3.6.8.
    20190928: Fixed bug in summarize() where darksky date filter would error if sensor times were not in darksky times.
              Fixed bug in summarize() if expected and acutal column names were not in sorted order.
    20191026: Improved handling of dataframe column naming to prevent potential issues with PurpleAir
              changing column names.
    20191101: Added Ipm25 column for "AQI". AQI in quotes since the offical midnight to midnight
              methodology is not used but a rolling 24 average is used instead.


  Notes for using reference files
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

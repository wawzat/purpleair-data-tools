""" 
pasc.py
 Prepares PurpleAir sensor historical data for further analysis.
    (csv files from www.purpleair.com/sensorlist).

 Description of operation:
    Iterates over all PurpleAir "primary" sensor csv files located in a user 
      specified data directory and combines them into files in various formats
      with re-ordered columns, UTC datetime conversion and 
      sensor LAT/LON coordinates.

      AQS / ARB Reference sensor and/or darksky wind data may also be
         optionally included.

         Note reference data functionality is a work in progress and limited
            to only specific stations at this time (Lake Elsinore and Norco)
            and only one station at a time.

    The combined data is resampled by averaging the readings over a specified
      interval and saved as new summarized Excel and/or csv file(s) as selected
      by the user (see command line arguments below).

    See the README.txt file for more details.

 FOR USER: See ---USER VARIABLES--- section below for variables that must be
   changed prior to running the program.


 Usage:  python pasc.py [-d <data directory>] [-r] [-w] [-k]
   [-s <summary interval>] [-l] [-o <output <type(s)>]
   [-p] [-y <yaxis scale (integer)>] [-f]

   -d argument enter existing "data directory" without path. e.g. "data5".
   -r option include AQS / ARB station reference data.
   -w option include AQS / ARB station reference data and include wind
      data in summary output.
   -k option include darksky wind data in summary output.
   -s argument summary interval. e.g. "15min" or "1H" etc. 
      valid values are 'W' (week), 'D" (day), "H" (hour),
      "min" or "T" (min), "S" (second).
   -l option display a list of reference stations. This option supersedes other
      arguments and options.
   -o argument output type e.g. "csv", "xl", "retigo", "all", "none",
      "xl retigo", "csv xl".
   -p option generate a simple plot of PM2.5 vs time. Close the plot to end the
      script.
   -y argument integer set yaxis range of the plot. e.g. -y 75
   -f option output the combined sensor data files to combined_full.csv

   Example: "python pasc.py -d Data1 -s 1H -o retigo".
             Combines files in Data1, summarizes over 1-hour intervals and
             outputs a RETIGO csv file.
   Example: "python pasc.py -d Data1 -s 1H -o retigo -p -y 75"
             Same as above and then outputs a plot with a y-axis range of 75.
       -or:
            "python pasc.py" without one or more arguments will use the
             defaults defined in the argument defaults section.

   use with -h or --help for help.


 License: This code may be unconditionally modified, used and redistributed
          for any private or commercial purpose without limitation.

 Warranty: No warranty or guarantee is expressed or implied.

 Author: James S. Lucas, Temescal Valley CA - 20191006

"""

# ----------------------------START IMPORT SECTION-----------------------------

#import traceback
import sys
import glob
import os
from sys import stdout
from os.path import join, getsize
import io                        # Required for Python 3.x.
import six                       # Required for Python 3.x.
from functools import reduce     # Required for Python 3.x.
import re
from math import radians, degrees, cos, sin, asin, atan2, sqrt
from datetime import datetime, timedelta
import argparse
from pytz import timezone, FixedOffset    # Included in Pandas package.
import csv
from collections import defaultdict
import pandas as pd                       # Not included with base Python.
import matplotlib.pyplot as plt           # Not included with base Python.
from prettytable import PrettyTable       # Not included with base Python.

# ----------------------------END IMPORT SECTION-------------------------------


# -----------------------START USER VARIABLES SECTION--------------------------

# Timezone: Change local time zone if needed. Web Search "PYTZ time zone list"
# for a list of applicable codes.
local_tz = timezone('US/Pacific')

# Working Directory: Modify the user variable below to include the working
# for your particular system.
# This should be the path up to but not including the data directory.
#
# e.g., If the path up to the directory containing your data is
# c:\data\purple_air and the sub-directory containing the data is sc20190901.
#
#    Then you would remove the # and set the user_directory variable to 
#     user_directory = r'c:\data\purple_air'.
#    Set the data_directory variable to data_directory = user_directory.
#    Specify the data directory on the command line.
#       i.e., python pasc.py -d sc20190901
#
# Note the r is required before the string to denote it as a raw string so
# as to avoid issues with the \ escape character.

#user_directory = r' '
matrix5 = r'd:\Users\James\OneDrive\Documents\House\PurpleAir'
virtualbox = r'/media/sf_VM_Shared_Files/House/PurpleAir'
servitor = r'c:\Users\Jim\OneDrive\Documents\House\PurpleAir'
wsl_ubuntu_matrix5 = r'/mnt/d/Users/James/OneDrive/Documents/House/PurpleAir'
wsl_ubuntu_servitor = r'/mnt/c/Users/Jim/OneDrive/Documents/House/PurpleAir'

# Change this variable to point to the desired directory above. 
data_directory = wsl_ubuntu_servitor

csv_root_path = data_directory + os.path.sep

# Argument Defaults: Used in the get_arguments function.
directory_default = "Test3"
summary_default = "1H"
output_default = ["csv", "retigo"]

# ------------------------END USER VARIABLES SECTION---------------------------


def get_ref_station_coordinates():
    # Get AQMD regulatory reference station information from the 
    # pasc_ref_stations.csv file.
    try:
        fn = os.path.join(os.path.dirname(__file__), 'pasc_ref_stations.csv')
        station_coordinates = defaultdict(dict)
        headers = [
            'sensor_name', 'site_name', 'AQS_NO',
            'ARB_NO', 'Lat', 'Lon', 'Elev_M',
            'Address', 'filename_format'
            ]
        with io.open(fn, 'rt') as fp:
            reader = csv.DictReader(
                fp,
                fieldnames=headers,
                dialect='excel',
                skipinitialspace=True
                )
            next(reader)
            for rowdict in reader:
                if None in rowdict:
                    del rowdict[None]
                sensor_name = rowdict.pop("sensor_name")
                station_coordinates[sensor_name] = rowdict
        return station_coordinates
    except Exception as e:
        print(
            'get station coordinates error.'
            ' ensure file "pasc_ref_stations.csv"'
            ' exists in the same directory as pasc.py.'
            )
        print(e)


def list_ref_station_coordinates(station_coordinates):
    # Display a list of regulatory stations and related information on the 
    # screen.
    try:
        table = PrettyTable()
        table.field_names = [
            "Sensor Name", "Site Name", "Lat", "Lon",
            "Filename Format (where xx = wd, ws, 25 or te)"
            ]
        table.align = "l"
        for key, value in station_coordinates.items():
            table.add_row([
                key, station_coordinates[key]["site_name"],
                station_coordinates[key]["Lat"],
                station_coordinates[key]["Lon"],
                station_coordinates[key]["filename_format"]
                ])
        print(" ")
        print("reference sensor names and associated information.")
        print(table)
        print(
            "-l option supersedes other options and arguments."
            " exiting without changes."
            )
        sys.exit(1)

    except Exception as e:
        print("list reference station info error.")
        print(e)


def status_message(output_message, newline):
    #output_message format ("message text", newline (yes or no))
    if newline == "yes":
        stdout.write(
                "\r" + output_message 
                + "                                                           "
                )
        stdout.flush()
        stdout.write("\n")
    elif newline == "no":
        stdout.write(
                "\r" 
                + output_message 
                + "                                                           "
                )
        stdout.flush()


def get_arguments(csv_root_path,
                  directory_default, summary_default, output_default):
   # Get command line arguments if any.
   # Using formatter_class and metavar='' to clean up help output. 
   # -o argument "choices" are duplicated in the help output otherwise.
   # Defaults are set in the USER VARIABLES SECTION above.
   parser = argparse.ArgumentParser(
       description='combine and summarize PurpleAir historical data files.',
       prog='pasc',
       usage='%(prog)s [-d <data directory>] [-r] [-w] [-k]'
             '[-s <summary interval>] [-l] [-o output <type(s)>]'
             '[-p] [-y <range>] [-f] [-a]',
       formatter_class=argparse.RawDescriptionHelpFormatter,
       )
   g=parser.add_argument_group(title='arguments',
          description='''   -d, --directory <data directory>     optional.  enter existing <data directory> without path. edit pasc.py to define path.
   -r, --reference                      optional.  include reference sensor data. a specific file naming convention is required for the input files.
   -w, --wind                           optional.  include reference station wind data. summary interval will be reset to 1H. -k option will override.
   -k, --darksky                        optionsl.  uses darksky wind data. requires darksky data to be included in data folder as DSKY_station_merged.csv
   -s, --summary <summary interval>     optional.  enter <summary interval> 'W' (week), 'D" (day), "H" (hour), "min" or "T" (min), "S" (second). e.g. "2H"
   -l, --listref                        optional.  show list of reference station names and associated information. supersedes other options, program will exit.
   -o, --output <type(s)>               optional.  enter <types> options are csv, xl, retigo, none, all or a combination of two types (e.g. xl retigo).
   -p, --plot                           optional.  show plot at the end of the run, close the plot to exit the script.
   -y, --yaxis  <Y-axis range>          optional.  integer to set plot Y-axis range. omitting this argument will plot with auto ranged Y-axis.
   -f, --full                           optional.  write combined sensor data to file combined_full.csv
   -a, --analyze                        optional.  analyze source.
   -t, --stats                          optional.  show sensor stats.                                                                               ''')
   g.add_argument('-d', '--directory',
                    type=str,
                    default=directory_default,
                    metavar='',
                    dest='directory',
                    help=argparse.SUPPRESS)
   g.add_argument('-r', '--reference', action='store_true',
                    dest='reference',
                    help=argparse.SUPPRESS)
   g.add_argument('-w', '--wind', action='store_true',
                    dest='wind',
                    help=argparse.SUPPRESS)
   g.add_argument('-k', '--darksky', action='store_true',
                    dest='darksky',
                    help=argparse.SUPPRESS)
   g.add_argument('-s', '--summary',
                    type=str, 
                    default=summary_default,
                    metavar='',
                    dest='summary',
                    help=argparse.SUPPRESS)
   g.add_argument('-l', '--listref', action='store_true',
                    dest='listref',
                    help=argparse.SUPPRESS)
   g.add_argument('-o', '--output',
                    type=str,
                    default=output_default,
                    nargs = '*',
                    choices = [
                        'csv', 'xl', 'retigo', 'all', 'csv xl',
                        'xl csv', 'csv retigo', 'retigo csv',
                        'xl retigo', 'retigo xl', 'none'
                        ],
                    metavar='',
                    dest='output',
                    help=argparse.SUPPRESS)
   g.add_argument('-p', '--plot', action='store_true',
                    dest='plot',
                    help=argparse.SUPPRESS)
   g.add_argument('-y', '--yaxis',
                    type=int, 
                    metavar='',
                    dest='yaxis',
                    help=argparse.SUPPRESS)
   g.add_argument('-f', '--full', action='store_true',
                    dest='full',
                    help=argparse.SUPPRESS)
   g.add_argument('-a', '--analyze', action='store_true',
                    dest='source',
                    help=argparse.SUPPRESS)
   g.add_argument('-t', '--stats', action='store_true',
                    dest='stats',
                    help=argparse.SUPPRESS)
   args = parser.parse_args()
   if args.wind:
      if args.summary != "1H":
         print(" ")
         print(
             "warning! -w option overrides -s argument."
             " summary interval set to 1H."
             )
         args.summary = "1H"
   output_type = args.output
   csv_full_path = csv_root_path + args.directory + os.path.sep
   return(args, output_type, csv_full_path)


def arg_check(args):
    try:
        incompatible = False
        if args.wind and args.darksky:
            print("warning! -k option overrides -w option. -w option ignored.")
            incompatible = True
    except Exception as e:
        print(" ")
        print("error in arg_check() %s" % e)
        sys.exit(1)


def input_files_check(args, csv_full_path):
    try:
        missing_files = {}
        files_missing = False
        if not glob.glob(os.path.join(csv_full_path, "*Primary*.csv")):
            print("error! expected primary sensor CSV files not found in %s."
                  " exiting." % csv_full_path 
                  )
            sys.exit(1)
        elif args.reference:
            if not glob.glob(os.path.join(csv_full_path, "*REF_25.csv")):
                missing_files.update(r = "_REF")
                files_missing = True
        elif args.wind:
            if (
                not glob.glob(os.path.join(csv_full_path, "*REF_wd.csv"))
                or 
                not glob.glob(os.path.join(csv_full_path, "*REF_ws.csv"))
                ):
                missing_files.update(w = "_REF")
                files_missing = True
        elif args.darksky:
            if not glob.glob(os.path.join(csv_full_path, "*DSKY*.csv")):
                missing_files.update(k = "DSKY")
                files_missing = True
        if files_missing:
            for key, value in missing_files.items():
                print("expected %s file(s) required with -%s option not found."
                      % (value, key)
                      )
            print("exiting.")
            print(" ")    
            sys.exit(1)
    except Exception as e:
        print(" ")
        print("error in input_files_check() %s" % e)
        sys.exit(1)


def existing_output_files_check(args, output_type, csv_full_path):
    # Check if output files already exist, display the file names,
    # warn the user and allow the user to cancel. This is included in case
    # you have performed additional analysis on an existing output file and
    # don't want to lose your work.
    csv_combined_filename = "combined_full.csv"
    xl_output_filename = "combined_summarized_xl.xlsx"
    csv_output_filename = "combined_summarized_csv.csv"
    retigo_output_filename = "combined_summarized_retigo.csv"
    proceed = None
    files_exist = False
    combined_full_exist = False
    all_output_files = [
        csv_full_path+"{0}".format(i) for i in [
            csv_combined_filename, xl_output_filename,
            csv_output_filename, retigo_output_filename
            ]
        ]
    overwrite_output_files = []
    if "all" in output_type:
        output_type = []
        output_type = ["xl", "csv", "retigo"]
        if args.full:
            output_type.append("full")
        for prefix in output_type:
            for filename in all_output_files:
                if "_" + prefix in filename:
                    overwrite_output_files.append(filename)
    elif "none" in output_type:
        if args.full:
            output_type.append("full")
        for prefix in output_type:
            for filename in all_output_files:
                if "_" + prefix in filename:
                    overwrite_output_files.append(filename)
    else:
        if args.full:
            output_type.append("full")
        for prefix in output_type:
            for filename in all_output_files:
                if "_" + prefix in filename:
                    overwrite_output_files.append(filename)
    table = PrettyTable()
    table.field_names = ["Filename", "Date Modified"]
    table.align = "l"
    for filename in glob.glob(os.path.join(csv_full_path, "combined*.*")):
        if filename in overwrite_output_files:
            basename = os.path.basename(filename)
            table.add_row([
                basename,
                datetime.fromtimestamp(
                    os.path.getmtime(filename)
                        ).strftime('%Y-%m-%d %H:%M:%S')
                ])
            if "_full" in basename:
                combined_full_exist = True
            files_exist = True
    if files_exist:
        print(" ")
        print("existing output files in %s" % csv_full_path)
        print(table)
        print("warning! files listed above will be overwritten."
              " exit and rename files you want to keep."
              )
        proceed = six.moves.input("overwrite files? (y/n): ")
        if proceed == "y" or proceed == "n":
            print(" ")
            return proceed, combined_full_exist, output_type
        else:
            print("please enter y or n: ")
    else:
        proceed = "y"
        return proceed, combined_full_exist, output_type


def parse_path(filename, csv_full_path):
    try:
        # Parses the sensor "tag number" and lat/lon coordinates from a 
        # historical sensor csv filename.
        spc = filename.index(' ')
        dot = filename.index('.')
        open_paren = filename.index('(', dot-4) 
        closed_paren = filename.index(')', dot-4)
        tag_number = filename[len(csv_full_path):spc].strip().upper()
        parsed_coords = filename[open_paren+1:closed_paren].strip()
        spc = parsed_coords.index(' ')
        LAT_coord = parsed_coords[:spc].strip()
        LON_coord = parsed_coords[spc:].strip()
        return tag_number, LAT_coord, LON_coord
    except ValueError as e:
        # Something is wrong with the filename. Will use the first 7 filename
        # characters for Sensor and null values for lat/lon.
        stdout.write("\n")
        stdout.write("\n")
        print(str(e) + " for " + filename)
        print(
            "ensure filename has a space after the sensor name"
            " and/or a space between"
            " and/or () surrounding the lat/lon coordinates"
            )
        print(
            "example:"
            " Sensor_Name (33.79862382847811 -117.529689312442)"
            " Primary 09_30_2018 10_17_2018.csv"
            )
        print("continuing to process data")
        print(" ")
        tag_number = filename[
                len(csv_full_path):len(csv_full_path) + 7
                ].strip()
        LAT_coord = ""
        LON_coord = ""
        return tag_number, LAT_coord, LON_coord


def get_summary_interval(args):
    # Function to convert the -s argument to seconds. used in summarize() to
    # compare against raw data measurement interval and prevent up sampling.
    try:
        offset_values = {
            'W': 6048000, 'T': 60, 'min': 60,
            'H': 3600, 'S': 1, 'D': 86400
            }
        number_part = re.findall(r'(\d+)', args.summary)
        number_part = [ int(x) for x in number_part ]
        text_part = re.findall(r'(\D+)', args.summary)
        offset_mult = offset_values.get(text_part[0], 0)
        summary_interval_sec = number_part[0] * offset_mult
        return summary_interval_sec
    except Exception as e:
        print(" ")
        print(
            "well that didn't go as planned."
            "error in get_summary_interval() function: %s" % e
            )
        sys.exit(1)


def combine_primary(args, csv_full_path):
    try:
        # Combines data from the sensor CSV files, adds sensor coordinates and
        # sensor names and optionally writes the combined CSV file to disk
        csv_combined_filename = csv_full_path + "combined_full.csv"
        cols = [
            'DateTime_UTC', 'Sensor', 'PM1.0_CF_ATM_ug/m3',
            'PM2.5_CF_ATM_ug/m3', 'PM10.0_CF_ATM_ug/m3',
            'Lat', 'Lon', 'UptimeMinutes', 'ADC',
            'Temperature_F', 'Humidity_%', 'PM2.5_CF_1_ug/m3'
            ]
        mapping = ({"created_at": "DateTime_UTC"})
        li = []
        if glob.glob(os.path.join(csv_full_path, "*Primary*.csv")):
            combined_size = 0
            combined_count = 0
            for root, dirs, files in os.walk(csv_full_path):
                for name in files:
                    if "Primary" in name.split():
                        combined_size += getsize(join(root, name))
                        combined_count += 1
                break               # don't walk files in subdirectories
            remaining_size = combined_size
            remaining_count = combined_count
            filenames = os.path.join(csv_full_path, "*Primary*.csv")
            for filename in glob.glob(filenames):
                status_message(
                        "reading " 
                        + str(remaining_count)
                        + " primary sensor files / "
                        + '{:,}'.format(remaining_size)
                        + " bytes remaining.",
                        "no"
                        )
                remaining_size = remaining_size - os.path.getsize(filename)
                remaining_count -= 1
                tag_number, LAT_coord, LON_coord = parse_path(
                    filename, csv_full_path
                    )
                dfs = pd.read_csv(filename, index_col=None, header=0)
                assumed_fieldnames = [
                    'created_at', 'PM1.0_CF_ATM_ug/m3', 'PM2.5_CF_ATM_ug/m3',
                    'PM10.0_CF_ATM_ug/m3', 'UptimeMinutes', 'ADC',
                    'Temperature_F', 'Humidity_%', 'PM2.5_CF_1_ug/m3'
                    ]
                actual_fieldnames = dfs.columns.values.tolist()
                actual_fieldnames = [
                    x for x in actual_fieldnames if not x.startswith('Unnamed')
                    ]
                if ("entry_id" in actual_fieldnames and
                        "entry_id" not in assumed_fieldnames):
                    assumed_fieldnames.insert(1, 'entry_id')
                if '' in actual_fieldnames:
                    actual_fieldnames.remove('')
                if "RSSI_dbm" in actual_fieldnames:
                    assumed_fieldnames = [
                        s.replace('ADC', 'RSSI_dbm') for s in assumed_fieldnames
                        ]
                    dfs = dfs.rename(columns={"RSSI_dbm": "ADC"})
                if sorted(actual_fieldnames) != sorted(assumed_fieldnames):
                    print(" ")
                    print(" ")
                    print(sorted(assumed_fieldnames))
                    print(sorted(actual_fieldnames))
                    differences = str(set(assumed_fieldnames)
                                      - set(actual_fieldnames)
                                      )
                    print("difference: " + differences[4:len(differences)-1])
                    raise ValueError ("actual fieldnames are different than"
                                      " assumed fieldnames. exiting."
                                      )
                dfs['created_at'] = (
                    dfs['created_at'].apply(lambda x: x.rstrip(' UTC'))
                    )
                dfs['Sensor'] = tag_number
                dfs['Lat'] = float(LAT_coord)
                dfs['Lon'] = float(LON_coord)
                li.append(dfs)
            status_message(
                    "completed reading primary files: processed "
                    + str(combined_count)
                    + " primary sensor files / "
                    + '{:,}'.format(combined_size)
                    + " bytes.",
                    "yes"
                    )
            status_message("combining primary files.", "no")
            df_combined_primary = pd.concat(li, axis=0, sort=True)
            #print(df_combined_primary)
            df_combined_primary = df_combined_primary.rename(columns=mapping)
            df_combined_primary = df_combined_primary[cols]
            df_combined_primary['DateTime_UTC'] = (
                    pd.to_datetime(
                        df_combined_primary['DateTime_UTC'],
                        format='%Y-%m-%d %H:%M:%S'
                        )
                    )
            # Create dictionay of min / max dates for later use in filtering
            # reference and/or darksky data to match
            date_range = {
                'min_date': df_combined_primary['DateTime_UTC'].min().floor('h'),
                'max_date': df_combined_primary['DateTime_UTC'].max().ceil('h')
                }
            status_message("completed combining primary files.", "yes")
            if args.full and (not (args.reference or args.wind)):
                # write the combined sensor data to a csv file if user selected
                # -f option but hold off and write the data in get_reference() if
                # -r or -w selected because the file will then be written in
                # combine_reference().
                with open(csv_combined_filename, "w") as reference:
                    status_message("writing combined_full.csv file."
                                   "combine_primary()", "no"
                                   )
                    df_combined_primary.to_csv(
                        reference, index=False, date_format='%Y-%m-%d %H:%M:%S'
                        )
                    status_message("completed writing combined_full.csv file.",
                                   "yes"
                                   )
        else:
            raise ValueError (' error: no primary csv files found in "%s".'
                              ' try a different directory. exiting.'
                              % args.directory
                              )
        return df_combined_primary, date_range
    except Exception as e:
        print(" ")
        print("error in combine_primary() function: %s" % e)
        sys.exit(1)


def combine_reference(local_tz, args, csv_full_path,
                      station_coordinates, df_combined_primary,
                      date_range
                      ):
    # Runs only if the -r or -w option is set.
    # Combines data from downloaded AQMD regulatory stations and station
    #  coordinate information into a single file.
    # Looks for specifically named reference data csv's in the data folder,
    #  combines them and appends them to the combined primary data csv file.
    # See the README.txt file for more information on reference data file
    #  naming requirements.
    # Timestamps in the merged file are converted to UTC to be consistent with
    #  the combined Primary csv timestamps.
    # Reference station historical data from SCAQMD regulatory sites are not
    #  daylight savings corrected and are always in PST (UTC -8 hours). 
    #    This is accounted for when converting to UTC (fixed 8-hour offset).
    try:
        value_names = {
                "wd": "WindDirection",
                "ws": "WindSpeed",
                "25": "PM2.5_CF_ATM_ug/m3",
                "te": "Temperature_F"
                }
        dfs = []
        # Determine number of combined size of reference files.
        if glob.glob(os.path.join(csv_full_path, "*REF*.csv")):
            combined_size = 0
            combined_count = 0
            wind_files_count = 0
            for root, dirs, files in os.walk(csv_full_path):
                for name in files:
                    names = name.split()
                    if names[0].find("REF") != -1:
                        combined_size += getsize(join(root, name))
                        combined_count += 1
                        if names[0].find("wd") != -1:
                            wind_files_count += 1
                        if names[0].find("ws") != -1:
                            wind_files_count += 1
                break               # don't walk files in subdirectories
            remaining_size = combined_size
            remaining_count = combined_count
            # Build a list of dataframes from the reference files, merge
            # and append them to the combined primary dataframe
            for filename in glob.glob(os.path.join(csv_full_path, "*REF*.csv")):
                status_message(
                        "reading " 
                        + str(remaining_count)
                        + " reference files / "
                        + '{:,}'.format(remaining_size)
                        + " bytes remaining.",
                        "no"
                        )
                remaining_size = remaining_size - os.path.getsize(filename)
                remaining_count -= 1
                basename = os.path.basename(filename)
                underscore = basename.index('_')
                dot = basename.index('.')
                df = pd.read_csv(
                        filename,
                        index_col=["Date Time"],
                        usecols=["Date Time", "Value"],
                        parse_dates=["Date Time"]
                        )
                ref_val = str(
                    value_names.get(basename[len(basename)-6:dot].strip())
                    )
                df = df.rename(columns={"Value": ref_val})
                dfs.append(df)
            sensor_name = basename[:underscore].strip() + "_REF"
            csv_combined_filename = csv_full_path + "combined_full.csv"
            ref_output_filename = (
                csv_full_path + sensor_name[:-4] + "_station_merged.csv"
                )
            Lat = float(station_coordinates[sensor_name]['Lat'])
            Lon = float(station_coordinates[sensor_name]['Lon'])
            status_message(
                "completed reading reference files: processed " +
                str(combined_count) +
                " reference files / " +
                '{:,}'.format(combined_size) +
                " bytes.", "yes"
                )
            # Merge reference files
            status_message("merging reference files.", "no")
            df_merged_ref = (
                reduce(
                    lambda left, right: pd.merge(
                        left, right, left_index=True, right_index=True
                        ), dfs
                    )
                )
            df_merged_ref.index = pd.to_datetime(
                    df_merged_ref.index,
                    format='%Y-%m-%d %H:%M:%S'
                    ).tz_localize(
                            FixedOffset(-8*60),
                            ambiguous=True,
                            nonexistent='shift_forward'
                            ).tz_convert('UTC')
            df_merged_ref.index = df_merged_ref.index.rename("DateTime_UTC")
            df_merged_ref.insert(
                0, "Sensor", sensor_name, allow_duplicates=True
                )
            df_merged_ref.insert(
                len(df_merged_ref.columns), "Lat", Lat, allow_duplicates=True
                )
            df_merged_ref.insert(
                len(df_merged_ref.columns), "Lon", Lon, allow_duplicates=True
                )
            df_merged_ref = (
                df_merged_ref.loc[
                    date_range.get('min_date'):date_range.get('max_date')
                    ]
                )
            df_merged_ref.to_csv(
                ref_output_filename,
                index=True,
                date_format='%Y-%m-%d %H:%M:%S'
                )
            status_message("completed merging reference files.", "yes")
            # Append reference data to combined PA data
            status_message(
                "appending reference data to combined primary data.", "no"
                )
            df_merged_ref = (
                df_merged_ref.drop(["WindDirection", "WindSpeed"], axis=1)
                )
            df_merged_ref.index = df_merged_ref.index.tz_localize(None)
            df_merged_ref.reset_index(inplace=True)
            cols=([
                'DateTime_UTC', 'Sensor', 'PM1.0_CF_ATM_ug/m3',
                'PM2.5_CF_ATM_ug/m3', 'PM10.0_CF_ATM_ug/m3',
                'Lat', 'Lon', 'UptimeMinutes', 'ADC',
                'Temperature_F', 'Humidity_%', 'PM2.5_CF_1_ug/m3'
                ])
            df_merged_ref = df_merged_ref.reindex(columns=cols, copy=False)
            df_combined_primary = df_combined_primary.append(df_merged_ref)
            if args.full:
                with open(csv_combined_filename, "w") as reference:
                    status_message("writing combined_full.csv file.", "no")
                    df_combined_primary.to_csv(
                            reference,
                            index=False,
                            date_format='%Y-%m-%d %H:%M:%S'
                            )
                    status_message(
                        "completed writing combined_full.csv file.", "yes"
                        )

                status_message(
                    "completed appending reference data to primary data.",
                    "yes"
                    )
        else:
            raise ValueError (
                'error! no reference csv files found in "%s". exiting.'
                % args.directory
                )
        return sensor_name, df_combined_primary
    except Exception as e:
        print(" ")
        print(" error in combine_reference().")
        print(e)
        sys.exit(1)


def summarize(local_tz, args, output_type,
    csv_full_path, sensor_name, df_combined_primary, date_range):
    try:
        # Use Pandas to resample the data, set some formatting and create the
        # combined summarized Excel and/or csv file(s).
        # If the -k option is set, merge darksky wind data into the sensor data.
        xl_output_filename = csv_full_path + "combined_summarized_xl.xlsx"
        csv_output_filename = csv_full_path + "combined_summarized_csv.csv"
        retigo_output_filename = csv_full_path + "combined_summarized_retigo.csv"
        df_interval_output_filename = csv_full_path + "combined_full_interval.csv"
        darksky_wind_files_count = 0
        status_message("summarizing data.", "no")
        datetime_col_name = "DateTime_" + str(local_tz).replace("/","_")
        df = df_combined_primary
        df.set_index('DateTime_UTC', inplace=True)
        df.index = (
            pd.to_datetime(
                df.index, format='%Y-%m-%d %H:%M:%S'
                ).tz_localize('UTC').tz_convert(local_tz)
            )
        # Get the -s summary interval argument and compare to the raw sensor
        # data summary interval, error and exit if up sampling.
        summary_interval_sec = get_summary_interval(args)
        df_interval = df.copy()
        df_interval = df_interval.drop(df.columns.difference(['Sensor']), axis=1)
        df_interval['tvalue'] = df_interval.index
        df_interval['delta'] = (
            df_interval['tvalue']-df_interval['tvalue'].shift()
            ).fillna(pd.Timedelta(seconds=0))
        df_interval = df_interval[~df_interval.Sensor.str.contains("REF")]
        df_interval['delta_seconds'] = (
            df_interval['delta'].astype('timedelta64[s]')
            )
        df_interval = (
            df_interval[
                df_interval['delta_seconds'].between(10, 36000, inclusive=True)
                ]
            )
        interval_duration = df_interval['delta_seconds'].mean()
        df_interval = (
            df_interval[
                df_interval['delta_seconds'].between(
                    10, interval_duration*1.2, inclusive=True
                    )
                ]
            )
        interval_duration = df_interval['delta_seconds'].mean()
        if summary_interval_sec <= interval_duration:
            print(" ")
            print(" ")
            print('error! selected summary interval ({a} = {b:.0f} seconds) <'
                  ' sensor data interval ({c:.0f} seconds). retry with a'
                  ' larger interval. exiting.'
                  .format(
                    a=args.summary, b=summary_interval_sec, c=interval_duration
                    )
                  )
            sys.exit(1)
        if args.darksky:
            # Create df_dsky DataFrame.
            dsky_wind_filename = csv_full_path + "DSKY_station_merged.csv"
            df_dsky = pd.read_csv(dsky_wind_filename, index_col=[0])
            df_dsky.index = pd.to_datetime(
                    df_dsky.index,
                    format='%Y-%m-%d %H:%M:%S'
                    ).tz_localize('UTC')
            # Filter out data outside of the sensor date range.
            df_dsky.sort_index(inplace=True)
            df_dsky = df_dsky.loc[
                    date_range.get('min_date'):date_range.get('max_date')
                    ]
            df_dsky.index = pd.to_datetime(
                    df_dsky.index,
                    format='%Y-%m-%d %H:%M:%S'
                    ).tz_convert(local_tz)
            df_dsky = df_dsky.reset_index()
            df_dsky.rename(
                columns={"DateTime_UTC": datetime_col_name}, inplace=True
                )
            df_dsky = df_dsky[
                [datetime_col_name, 'WindDirection', 'WindSpeed']
                ]
        elif sensor_name != " " and args.wind:
            # Create df_wind DataFrame.
            ref_combined_filename = (csv_full_path 
                + sensor_name[:-4] 
                + "_station_merged.csv"
                )
            df_wind = pd.read_csv(ref_combined_filename, index_col=[0])
            df_wind.index = pd.to_datetime(
                    df_wind.index,
                    format='%Y-%m-%d %H:%M:%S'
                    ).tz_localize('UTC').tz_convert(local_tz)
            df_wind = df_wind.reset_index()
            df_wind.rename(
                columns={"DateTime_UTC": datetime_col_name}, inplace=True
                )
            df_wind = df_wind[[datetime_col_name, 'WindDirection', 'WindSpeed']]
        df2 = df.groupby('Sensor')
        df3 = df2.resample(args.summary).mean()
        #df3 is used for the summary output files
        df3 = df3.reset_index()                  
        # filter PM2.5 between 0-1000
        df3 = df3[df3['PM2.5_CF_ATM_ug/m3'].between(0, 1000, inclusive=True)]  
        df3.rename(columns={"DateTime_UTC": datetime_col_name}, inplace=True)
        if args.darksky:
            df3 = df3.merge(df_dsky, how='left', on=datetime_col_name)
        elif sensor_name != " " and args.wind:
            df3 = df3.merge(df_wind, how='left', on=datetime_col_name)
        df_summary = df3.copy()
        status_message("completed summarizing data.", "yes")
        if "xl" in output_type:
            status_message(
                    "processing output files."
                    " this may take awhile due to Excel output type.",
                    "no"
                    )
        else:
            status_message("processing output files.", "no")
        # csv format
        if "csv" in output_type or "all" in output_type:
            df3.to_csv(
                    csv_output_filename,
                    index=False,
                    date_format='%Y-%m-%d %H:%M:%S'
                    )
        # Excel format
        if "xl" in output_type or "all" in output_type:
            df_xl = df3.copy()
            df_xl[datetime_col_name] = (
                df_xl[datetime_col_name].dt.tz_localize(None)
                )
            writer_xlsx = pd.ExcelWriter(
                    xl_output_filename,
                    engine='xlsxwriter',
                    options={'remove_timezone': True}
                    )
            df_xl.to_excel(
                writer_xlsx, 'Sheet1', index=False, merge_cells=False
                )
            workbook = writer_xlsx.book
            worksheet = writer_xlsx.sheets['Sheet1']
            format1 = workbook.add_format({'num_format': 'Y-m-d h:mm:ss'})
            format2 = workbook.add_format({'num_format': '#,##0.00'})
            format3 = workbook.add_format({'num_format': '#,##0.000000'})
            worksheet.set_column('B:B', 22, format1)
            worksheet.set_column('C:C', 23, format2)
            worksheet.set_column('D:D', 23, format2)
            worksheet.set_column('E:E', 23, format2)
            worksheet.set_column('F:F', 13, format3)
            worksheet.set_column('G:G', 13, format3)
            worksheet.set_column('H:H', 18, format2)
            worksheet.set_column('I:I', 12, format2)
            worksheet.set_column('J:J', 16, format2)
            worksheet.set_column('K:K', 16, format2)
            worksheet.set_column('L:L', 23, format2)
            worksheet.set_column('M:M', 15, format2)
            worksheet.set_column('N:N', 15, format2)
            worksheet.freeze_panes(1, 0)
            writer_xlsx.save()
        status_message("completed processing output files.", "yes")
        status_message(
                "sensor data processed from: " 
                + str(date_range.get('min_date')) 
                + " through " 
                + str(date_range.get('max_date')),
                "yes"
                )
        df_raw_stats = (
            df['PM2.5_CF_ATM_ug/m3']
            .describe().apply(lambda x: format(x, '.2f'))
            )
        df_summary_stats = (
            df3['PM2.5_CF_ATM_ug/m3']
            .describe().apply(lambda x: format(x, '.2f'))
            )
        df_stats = pd.concat(
            [df_raw_stats, df_summary_stats], axis=1, join='inner'
            )
        df_stats.columns = ['Raw', 'Summarized']
        # EPA Real Time Geospatial Data Viewer (RETIGO) csv format
        # Note: Rows with null coordinate values are dropped
        if "retigo" in output_type or "all" in output_type:
            if args.wind or args.darksky:
                mapping = ({
                    "DateTime_" + str(local_tz).replace("/","_"): "Timestamp",
                    "Lon": "EAST_LONGITUDE(deg)",
                    "Lat": "NORTH_LATITUDE(deg)",
                    "Sensor": "ID(-)",
                    "PM1.0_CF_ATM_ug/m3": "PM1.0",
                    "PM2.5_CF_ATM_ug/m3": "PM2.5",
                    "PM10.0_CF_ATM_ug/m3": "PM10.0",
                    "Temperature_F": "Temperature",
                    "Humidity_%": "Relative Humidity",
                    "WindSpeed": "wind_magnitude(m/s)",
                    "WindDirection": "wind_direction(deg)"
                    })
                cols = ([
                    'Timestamp', 'EAST_LONGITUDE(deg)', 'NORTH_LATITUDE(deg)',
                    'ID(-)', 'PM1.0', 'PM2.5', 'PM10.0', 'Temperature',
                    'Relative Humidity', 'wind_magnitude(m/s)',
                    'wind_direction(deg)'
                    ])
            else:
                mapping = ({
                    "DateTime_" + str(local_tz).replace("/","_"): "Timestamp",
                    "Lon": "EAST_LONGITUDE(deg)",
                    "Lat": "NORTH_LATITUDE(deg)",
                    "Sensor": "ID(-)",
                    "PM1.0_CF_ATM_ug/m3": "PM1.0",
                    "PM2.5_CF_ATM_ug/m3": "PM2.5",
                    "PM10.0_CF_ATM_ug/m3": "PM10.0",
                    "Temperature_F": "Temperature",
                    "Humidity_%": "Relative Humidity"
                    })
                cols = ([
                    'Timestamp', 'EAST_LONGITUDE(deg)', 'NORTH_LATITUDE(deg)',
                    'ID(-)', 'PM1.0', 'PM2.5', 'PM10.0', 'Temperature',
                    'Relative Humidity'
                    ])
            df3 = df3.rename(columns=mapping)
            df3 = df3.drop(["UptimeMinutes", "ADC", "PM2.5_CF_1_ug/m3"], axis=1)
            df3 = df3[cols]
            df3 = df3.drop([
                "PM1.0", "PM10.0",
                "Temperature", "Relative Humidity"
                ], axis=1)
            df3 = df3[df3['EAST_LONGITUDE(deg)'].notnull()]
            if args.wind or args.darksky:
                df3 = df3[df3['wind_magnitude(m/s)'].notnull()]
                # Convert from mph to m/s.
                df3['wind_magnitude(m/s)'] = (
                    df3['wind_magnitude(m/s)'] / 2.23693629
                    )
            df3.to_csv(
                retigo_output_filename,
                index=False,
                date_format='%Y-%m-%dT%H:%M:%S%z',
                header=True
                )
        print(" ")
        status_message("PM2.5 Statistics", "yes")
        print(df_stats)
        print(" ")
        return df, df_summary
    except IOError as e:
        print (str(e) + ". exiting without changes.")
    except Exception as e:
        print(" ")
        print("error in summarize() function: %s" % e)
        #traceback.print_exc(file=sys.stdout)
        sys.exit(1)


def df_plot(args, sensor_name, df):
    try:
        # Show plot of summarized data. Close plot window to end script.
        plot_axis_limits = (0,args.yaxis)
        print("generating plot. close plot to exit script.")
        df.index = df.index.rename('Timestamp')
        df2 = df.groupby('Sensor')
        df3 = df2.resample(args.summary).mean()
        df3 = df3.drop([
            "Lon", "Lat", "PM1.0_CF_ATM_ug/m3",
            "PM10.0_CF_ATM_ug/m3", "Temperature_F",
            "Humidity_%"
            ],
            axis=1)
        mapping = {"PM2.5_CF_ATM_ug/m3": "PM2.5"}
        df3 = df3.rename(columns=mapping)
        df3 = df3.reset_index()
        cols = ['Timestamp', 'Sensor', 'PM2.5']
        df3 = df3[cols]
        df3.set_index('Timestamp', inplace=True)
        if args.reference or args.wind:
            df4 = df3[df3.Sensor == sensor_name]
            df3 = df3[df3.Sensor != sensor_name]
            df4 = df4.loc[df3.index.min():df3.index.max()]
            df3 = df3.pivot(columns='Sensor', values='PM2.5')
            df4 = df4.pivot(columns='Sensor', values='PM2.5')
            ax = df3.plot(
                ylim=plot_axis_limits, color='gray', alpha=0.1, title='PM2.5'
                )
            df4.plot(ylim=plot_axis_limits, color='yellow', alpha=0.5, ax=ax)
            plt.ylabel('ug/M^3')
            plt.show()
        else:
            df3 = df3.pivot(columns='Sensor', values='PM2.5')
            df3.plot(
                ylim=plot_axis_limits, color='gray', alpha=0.1, title='PM2.5'
                )
            plt.ylabel('ug/M^3')
            plt.show()
    except IOError as e:
        print (str(e) + ". exiting without changes.")


def sensor_stats(csv_full_path, df):
    stats_output_filename = csv_full_path + 'sensor_stats.csv'
    df_stats = df.copy()
    #print(df_stats)
    df_stats.reset_index(inplace=True)
    df_stats = df_stats.sort_values('DateTime_UTC').groupby('Sensor')['DateTime_UTC'].agg(['first','last'])
    print(df_stats)
    df_stats.to_csv(
            stats_output_filename,
            index=True,
            date_format='%Y-%m-%d %H:%M:%S',
            header=True
            )


def analyze_source(csv_full_path, df_summary):
    # Compute bearing and distance from each sensor to a fixed coordinate
    # (hard coded coordinate) and determine if each sensor is "upwind" or
    # "downwind" from the fixed coordinate. This is beta may be flawed.
    try:
        status_message("computing sensor bearing and distance.", "yes")
        source_output_filename = csv_full_path + "source.csv"
        df_source2 = df_summary.copy()
        source_coords = {'Lat': 33.7555312, 'Lon': -117.481027}

        df_source2['source_dist'] = df_source2.apply(
            lambda x: haversine_dist(x['Lat'], x['Lon'],
            source_coords.get('Lat', 0),
            source_coords.get('Lon', 0)),
            axis=1
            )
        df_source2['source_bear'] = df_source2.apply(
            lambda x: bearing(x['Lat'], x['Lon'],
            source_coords.get('Lat', 0),
            source_coords.get('Lon', 0)),
            axis=1
            )
        df_source2['WindVector'] = df_source2.apply(
            lambda x: (x['WindDirection']+180)%360,
            axis=1
            )
        df_source2['wind_side'] = df_source2.apply(
            lambda x : 'downwind'
            if x['source_bear'] >= (x['WindVector'] - 22.5) % 360
            and x['source_bear'] <= (x['WindVector'] + 22.5) % 360
            else 'upwind', axis=1
            )
        cols = [
            'Sensor', 'Lat', 'Lon', 'source_dist',
            'source_bear', 'WindVector', 'WindSpeed',
            'wind_side'
            ]
        print(df_source2[cols])
        df_source2.to_csv(
                source_output_filename,
                index=False,
                date_format='%Y-%m-%d %H:%M:%S',
                header=True
                )
        status_message("completed computing sensor bearing and distance.", "yes")
    except Exception as e:
        print(" ")
        print("error in analyze_source() function: %s" % e)
        sys.exit(1)


def haversine_dist(lat1, lon1, lat2, lon2):
    try:
        # This is in miles. For Earth radius in kilometers use R = 6372.8.
        R = 3959.87433 
        dLat = radians(lat2 - lat1)
        dLon = radians(lon2 - lon1)
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
        c = 2*asin(sqrt(a))
        return round(R*c, 2)
    except Exception as e:
        print(" ")
        print("error in haversine_dist() function: %s" % e)
        sys.exit(1)


def bearing(lat1, lon1, lat2, lon2):
    try:
        #dLat = radians(lat2 - lat1)
        dLon = radians(lon2 - lon1)
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        y = sin(dLon) * cos(lat2)
        x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dLon)
        bearing = (degrees(atan2(y, x)) + 180) % 360
        return round(bearing, 2)
    except Exception as e:
        print(" ")
        print("error in bearing() function: %s" % e)
        sys.exit(1)


# ---Main---
args, output_type, csv_full_path = get_arguments(
        csv_root_path,
        directory_default,
        summary_default,
        output_default
        )
station_coordinates = get_ref_station_coordinates()
if args.listref:
    list_ref_station_coordinates(station_coordinates)
else:
    arg_check(args)
    input_files_check(args, csv_full_path)
    proceed, combined_full_exist, output_type = existing_output_files_check(
        args, output_type, csv_full_path
        )
    if proceed == "y":
        df_combined_primary, date_range = combine_primary(args, csv_full_path)
        if args.reference or args.wind:
            sensor_name, df_combined_primary = combine_reference(
                    local_tz, args,
                    csv_full_path,
                    station_coordinates,
                    df_combined_primary,
                    date_range
                    )
        else:
            sensor_name = " "
        df, df_summary = summarize(
                local_tz,
                args,
                output_type,
                csv_full_path,
                sensor_name,
                df_combined_primary,
                date_range
                )
        if args.plot:
            df_plot(args, sensor_name, df)
        if args.stats:
            sensor_stats(csv_full_path, df)
        if args.source:
            analyze_source(csv_full_path, df_summary)
    elif proceed == "n":
        print("exiting without changes.")

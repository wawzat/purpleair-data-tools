from pytz import timezone


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
#    Then you would set the user_directory variable to 
#     user_directory = r'c:\data\purple_air'.
#    Set the data_directory variable to data_directory = user_directory.
#    Specify the data directory on the command line.
#       i.e., python pasc.py -d sc20190901
#
# Note the r is required before the string to denote it as a raw string
# to avoid issues with the \ escape character.


#user_directory = r' '
matrix5 = r'd:\Users\Jim\OneDrive\Documents\House\PurpleAir'
virtualbox = r'/media/sf_PurpleAir'
servitor = r'c:\Users\Jim\OneDrive\Documents\House\PurpleAir'
wsl_ubuntu_matrix5 = r'/mnt/d/Users/James/OneDrive/Documents/House/PurpleAir'
wsl_ubuntu_servitor = r'/mnt/c/Users/Jim/OneDrive/Documents/House/PurpleAir'

# Change this variable to point to the desired directory above. 
data_directory = matrix5

# Argument Defaults: Used in the get_arguments function.
directory_default = "Test3"
summary_default = "1H"
output_default = ["csv", "retigo"]

# ------------------------END USER VARIABLES SECTION---------------------------

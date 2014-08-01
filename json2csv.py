# Reads tweets, stored in json format in compressed text files (one tweet per line) and creates a
# CSV file from the output. Data to be extracted can be chosen using the command-line, but if there
# are no arguments then default commonly-used fields will be extracted. THese are:
#
# Tweet_ID, User_ID, Screen_Name, Lat, Lon, Loc_Txt, Time, Text
#
# Note: for convenience some time columns are also added: Year, Month, Day, Hour, Minute, Seconds

import argparse # For parsing command line arguments
import gzip # For compressing files
import os
import json
import sys

import datetime as dt
# Can't use dt.strptime() to convert time string to date because %z isn't valid! Instead use this:
import email.utils 
# NOTE ABOUT TIME ZONES: I'm using local time, not UTC. So there will be two kinks in the data when
# UK changes time zone. Advantage is that work patterns are constant (e.g. 9am-5pm) so don't want to
# change these when the time zone changes.

def fix(text):
    """Encodes a string as unicode and replaces difficult characters. Also checks for and removes
    things that will break the csv file like newline characters.
    Also adds quote characters around strings.
    If the given 'text' doesn't have an encode method (e.g. it is a number) then it is just returned
    as a string (using str)."""
    try: 
        return '"'+text.encode(encoding='UTF-8', errors='xmlcharrefreplace').replace("\n"," ")+'"'
    except AttributeError:
        return str(text)



# A list to store the fields to retrieve from the json files. Start with some commonly used fields.
# Each dimension needs to be separated with commas
fields = [
        "id",                   # ID of the tweet
        "user,id",              # ID of the user
        "user,screen_name",     # Name of the user
        "geo,coordinates,0",    # Latitude (y)
        "geo,coordinates,1",    # Longitude (x)
        "place,full_name",      # Name of the location
        "created_at",           # Time created
        "text"                  # Message text
        ]

# ****** Create the command-line parser ******
parser = argparse.ArgumentParser(description='Convert JSON tweets to CSV.')

# Filenames
parser.add_argument('files', nargs="+", metavar="FILE",
        help="List of input files (at least one must be specified")
parser.add_argument('-o', '--outfile', default="tweets.csv",
        help="Output file name (default tweets.csv")

# Specify fields to extract
parser.add_argument('-f', '--field', nargs=1,
        help="Add a field to the output, with each dimension separated by commas. \
                E.g. to get the ID of the user who posted the message, use 'user,id'.")

# Whether or not to clear all the defaults or add time columns
parser.add_argument('-nd', '--no_defaults', action="store_true", default=False,
        help="Don't add any of the default fields to the CSV output")
parser.add_argument('-ntc', '--no_time_columns', action="store_true", default=False,
        help="Don't add the extra time columns to the CSV output")


# Parse command-line arguments
args = parser.parse_args()

if args.no_defaults:
    print "-nd specified: not extracting the default fields"
    fields = {}

# XXXX add any specified columns to the fields that we're interested in

if len(fields)==0:
    print "No fields have been specified, you have probably set the '--no_defaults' flag "+\
            "but not specified any of your own fields.\n"+\
            "This is probably a mistake so I wont continue.\n"+\
            "If you want to add fields yourself use --field"
    sys.exit(1)

print "Will write output to: ",args.outfile

print "Will extract data in the following json fields: ",fields

print "Will {s} time columns".format(s="not add" if args.no_time_columns else "add")



# ****** Start interrogating the tweet files (one tweet per line, possibly compressed) ******

with open(args.outfile, 'w') as of:

    for i, fname in enumerate(args.files):
        # work out if it is a compressed file or plain text and then open as a file object called
        # 'f'. (gzip and normal files can be treated the same)
        with GzipFile(fname, mode="rb") if fname[:-3] == ".gz" else open(fname, "r") as f:

        #f = None
        #if fname[:-3] == ".gz":
        #    f = GzipFile(fname, mode="rb")
        #else
        # There is no data for this field in this tweet:
        #    f = open(fname, "r")

            print "Interrogating file {i}/{num}: {f}".format(i=(i+1), num=len(args.files), f=f.name)

            # If this is the first file, prepare the output file
            if i==0:
                for field in fields:
                    of.write(field.replace(",","-") +", ") # (note: no commas in fieldnames)
                # Also add the extra time columns (added for convenience)
                if not args.no_time_columns:
                    of.write("Year, Month, Day, Hour, Minute, Seconds")
                of.write("\n")

            for line in f:
                tweet = json.loads(line) # Create a dictionary from the tweet on the current line
                
                # For each field that we're interested in, extract the data and write to the file
                for field in fields:
                    nodata = False # Set to true if there is no data for this field
                    # Need to do a multi-dimensional dictionary lookup from the string field (Sam P
                    # helped me with this). I.e. convert 's = "user,name,firstname" to 
                    # tweet["user"]["name"]["firstname"]
                    value = tweet
                    #print "\n* FIELD: {f}\n".format(f=field)
                    for key in field.split(","):
                        #print "KEY:",key, "\nVALUE",value
                        if value == None:# or key not in value:
                            # There is no data for this field in this tweet
                            print "No data in tweet for field: {f}".format(f=field)
                            print "Value: '{v}'. Key: '{k}'".format(v=value, k=key)
                            nodata = True
                            continue # Move onto the next field
                        try:
                            value = value[key]
                        except TypeError: 
                            # This happens if the key should be an integer. E.g. with coordinates,
                            # instead of being a dictionary they are a two-element list
                            value = value[int(key)]


                    if nodata:
                        of.write(" , ") # Nothing to write for this field
                    else:
                        of.write(fix(value)+", ")

                # Have added all the required fields, now add time columns for convenience.This is
                # much more complicated than it should be because the %z symbol in strftime()
                # doesn't work on my mac, might work on unix. Instead use email.util library (!)

                time_str = tweet['created_at']
                # Make a tuple from the time (e.g. (year,month,day,hour,minute,second)
                time_tpl = email.utils.parsedate_tz(time_str) 
                # Now use those indivdual components to make a datetime object
                time = dt.datetime(*[time_tpl[i] for i in range(7)]) 

                print time_str, time
                XXXX HERE ADD Separat columns for month etc...

                of.write("\n") # Finished this message, on to next one







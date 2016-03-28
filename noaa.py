#!/usr/bin/python
"""
Copyright (C) 2016 William Ziener-Dignazio

NOAA Tidal Data Retriever

Usage: python noaa.py

This program uses the exposed public API via noaa.gov to build a CSV file
consisting of tidal data since January 1, 2000 to the current date.

The online NOAA api has a max retrieval period of approximately 1 day, thus
we must iteratively retrieve the tidal through consecutive API calls. The
API calls themselves are through HTTP requests to a specificied endpoint
retrieved from the noaa.gov website. The enpoint URL is hardcoded below
(as 'url') with substitution points for the desired date ranges.

As a courtesy to the NOAA servers, we limit requests to 1 per second. This
both prevents heavy load to the government run servers, and avoids blacklisting
of the executing IP address, which with enough requests might look like a
DOS attack.

Output files are of the format: "tidal_data-${DATETIME}.csv"

Every time the tool is run, a new file will be generated, as to not destroy
previous runs that generated data csv files.

"""
from datetime import timedelta, date
from string import Template
import pycurl
from StringIO import StringIO
import time
import sys

# Date format : YYYYMMDD, substitute begin_date and end_date
url = 'http://tidesandcurrents.noaa.gov/api/datagetter?product=water_level&application=NOS.COOPS.TAC.WL&begin_date=$begin_date&end_date=$end_date&datum=MLLW&station=1617760&time_zone=GMT&units=english&format=csv'

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

start_date = date(2000, 1, 1)
end_date = date(date.today().year, date.today().month, date.today().day)

delta = end_date - start_date

print "Start Date: " + str(start_date)
print "End Date: " + str(end_date)
print "Total days: " + str(delta)

print "Starting download of NOAA tidal data..."

file = open('tidal_data-' + str(time.time()) + '.csv', 'w+', 1024)
write_header = True

days_traversed = 0
for single_date in daterange(start_date, end_date):
    start_date_past = single_date - timedelta(days=1)
    end_date_past = single_date

    s = Template(url)
    curl_url = s.substitute(begin_date=start_date_past.strftime("%Y%m%d"),
                            end_date=end_date_past.strftime("%Y%m%d"))

    buffer = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, curl_url)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()

    body = buffer.getvalue()
    if write_header:
        file.write(str(body))
        write_header = False
    else:
        file.write("\n".join(str(body).splitlines()[1:]))
        file.write("\n")
    
    time.sleep(1)
    days_traversed += 1

    percentComplete = float(days_traversed) / float(delta.days)
    print '\r>> %f%% Complete' % percentComplete,
    sys.stdout.flush()

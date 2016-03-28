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

"""
As mentioned above, this "magic" URL corresponds with the API for retrieving water
level tidal data from the NOAA API endpoint.

This value will be handed to the pycurl library, which will issue a GET request
against the enpoint, retrieving a portion of CSV data for us.

This URL is broken down into the following components:

1. NOAA subdomain for tidal and current data
2. API call to water_level via the specified application
3. Enter in begin and end dates by substitution values
4. Provide station number (station in hawaii)
5. Request CSV format

"""
url = 'http://tidesandcurrents.noaa.gov/api/datagetter?' + \
      'product=water_level&application=NOS.COOPS.TAC.WL&' + \
      'begin_date=$begin_date&end_date=$end_date&' + \
      'datum=MLLW&station=1617760&time_zone=GMT&units=english&' + \
      'format=csv'

"""
Generator function that produces the next day within the date range,
iterating once on every method call.
"""
def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

"""
This is a close approximation of the start date from which NOAA started giving
their tidal data to the public. We might be able to tweak it to a slightly further,
date, but for data mining purposes this should be sufficient.
"""
start_date = date(2000, 1, 1)
end_date = date(date.today().year, date.today().month, date.today().day)

delta = end_date - start_date # Amount of time passed from today to the start_date

print "Starting download of NOAA tidal data..."

"""
Open up a file descriptor for the tidal_data-${DATETIME}.csv file,
with a buffer of 1024 bytes. This allows the data to be slightly
buffered before hitting disk. The Requests themselves are probably
smaller than the file buffer; as long as we don't kill -9 the process,
we'll probably not lose any data.
"""
file = open('tidal_data-' + str(time.time()) + '.csv', 'w+', 1024)
write_header = True

"""
Main retrieval loop

We iterate over the date range, from start date (January 1st, 2000) to
the end date (Today). Along the way, we substitute the day values for
the current iteration into the template "url".

We use pycurl to orchestrate the GET request against the NOAA enpoint,
and create a new instance of a library request every iteration. 

The response to the request is stripped of metadata provided from the request,
and then written to the output CSV file on disk.

We maintain a percentage counter that is updated every iteration, to
track how far we've gone.
"""
days_traversed = 0
for single_date in daterange(start_date, end_date):
    start_date_past = single_date - timedelta(days=1)
    end_date_past = single_date

    """
    We take our hardcoded template url, and substitute in the values
    corresponding to the iterations day. Remember that we are limited to
    retrieving approx. 1 days worth of data at a time.
    """
    s = Template(url)
    curl_url = s.substitute(begin_date=start_date_past.strftime("%Y%m%d"),
                            end_date=end_date_past.strftime("%Y%m%d"))

    """
    Build up a python StringIO buffer, allowing us to write python string
    data to an underyling byte buffer.
    """
    buffer = StringIO()

    """
    Create an instance of a pycurl Curl object, this will be our interface
    to the libcurl library. We must set some configuration options so that
    we can request against the correct location.
    """
    c = pycurl.Curl()
    c.setopt(c.URL, curl_url)		# Set the completed url template as the target
    c.setopt(c.WRITEDATA, buffer)	# The response shall go to our string buffer
    c.perform()				# Execute the request
    c.close()				# Finish up the Curl object

    """
    Now that we have processed the request, get the value of the body, and save
    it to the output csv file.
    """
    body = buffer.getvalue()
    if write_header:
        """
        On the first run, we want to include the header line that describes the
        column values. We don't want to include these on subsequent runs.
        """
        file.write(str(body))
        write_header = False
    else:
        file.write("\n".join(str(body).splitlines()[1:])) # Doesn't include header line
        file.write("\n")
        
    """
    XXX: Caution changing this value
    
    We sleep for a second so that we do not bombard the NOAA API endpoints with requests
    for data. Doing so puts strain on their resources, as well as increases the chance that
    your IP address will be blacklisted by their servers.
    """
    time.sleep(1)
    days_traversed += 1

    percentComplete = float(days_traversed) / float(delta.days)
    print '\r>> %f%% Complete' % percentComplete,
    sys.stdout.flush()

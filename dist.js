/*
 * Moon Distance Calculator for Tidal Data
 * Copyright 2016 William Ziener-Dignazio
 *
 * Usage: node dist.js <tidal_data-XXX.csv>
 */
var buffer = require('buffer');
var SunCalc = require('suncalc');
var csv = require('fast-csv');
var fs = require('fs');

/*
 * These values correspond to the tidal station we pull from noaa.py,
 * by providing these we can handoff the lat and lon to the SunCalc library.
 */
const HILO_STATION_LAT = 19.718888888888888
const HILO_STATION_LON = -155.05083333333334
const BUFFER_SIZE=4096

if (process.argv.length != 3) {
    console.error("Usage: node dist.js <tidal_data-XXX.csv>");
    process.exit();
}

var inStream = fs.createReadStream(process.argv[2])
var outStream = fs.createWriteStream("lunar_distance-" +
				     (process.argv[2].split("-")[1].split(".")[0]) +
				     ".csv")

/* Write out the header for the CSV File */
outStream.write("Date,Distance (KM)\n")

/*
 * Output buffer, I tried piping one line at a time, but it
 * was incredibly slow. So we're going to try buffering it up in
 * memory a bit, then writing it out.
 */
var outBuffer = new Buffer(BUFFER_SIZE)
var bufferWritten = 0

var csvStream = csv()
    .on('data', function(data) {
	var date = new Date(data[0]);
	var distance = SunCalc.getMoonPosition(date, HILO_STATION_LAT, HILO_STATION_LON).distance;
	var outString = data[0] + "," + distance + "\n"

	if ((bufferWritten + outString.length) >= BUFFER_SIZE) {
	    outStream.write(outBuffer.toString("utf-8", 0, bufferWritten))
	    outBuffer = new Buffer(BUFFER_SIZE)
	    bufferWritten = 0
	}

	outBuffer.write(outString, bufferWritten, outString.length, "utf-8")
	bufferWritten += outString.length
    })
    .on('end', function() {
	console.log(bufferWritten)
	outStream.write(outBuffer.toString("utf-8", 0, bufferWritten))
	console.log ("#### Done ####")
    });

/* Start the feed process */
inStream.pipe(csvStream);

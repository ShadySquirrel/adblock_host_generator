#!/usr/bin/python2

import urllib
import os
import sys
import time

# update_progress() : Displays or updates a console progress bar
## Accepts a float between 0 and 1. Any int will be converted to a float.
## A value under 0 represents a 'halt'.
## A value at 1 or bigger represents 100%
#
# Function taken from https://stackoverflow.com/a/15860757, slightly modified to fit my needs
# modifications include support for description text (instead of "Percent" used in original)
# and little bit fixed formating (description is fixed-width, making things nicer)

def update_progress(action, progress):
    barLength = 50 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "\r\n"
    if progress < 0:
        progress = 0
        status = "\r\n"
    if progress >= 1:
        progress = 1
        status = "\r\n"
    block = int(round(barLength*progress))
    text = "\r{0:58} [{1}] {2}% {3}".format( action, "#"*block + "-"*(barLength-block), round(progress*100,2), status)
    sys.stdout.write(text)
    sys.stdout.flush()
	
# first, configuration.
HOSTS_FILENAME = "adblock_list_domains.txt"
HOSTS_ONLINE = True
HOSTS_URL = "https://raw.githubusercontent.com/ShadySquirrel/adblock_host_generator/master/adblock_list_domains.txt"
TARGET_FILE = "generated_hosts.txt"
DATABASE_AGE = 7
USE_CACHE = True
CACHE_AGE = 1
CACHE_PATH = "cache"

# function to check how old is that file.
def check_age(file, max_age):
	now = time.time()
	if os.path.isfile(file):
		created = os.path.getmtime(file)
	else:
		created = 0
	old_age = now - 60*60*24*max_age
	
	# guess that file is always newer than max_age, and return False.
	state = False
	
	# now, do a check if file is really newer than max_age, and change state according to that.
	if created < old_age:
		state = True
		
	return state

def generate_banner():
	import datetime
	
	time_now = datetime.datetime.now()
	
	banner_string = "###########################################################################\n"
	banner_string += "# Generated on %s\n" % time_now
	banner_string += "# Contains hosts from:\n"

	for url in content:
		banner_string += "# %s (%s) \n" % (url[1], url[0])
	
	banner_string += "###########################################################################\n"
	
	return banner_string
	
# grab domain list file if online
if HOSTS_ONLINE:
	to_download = False
	if not os.path.isfile(HOSTS_FILENAME):
		print("* Hosts database not found, downloading from %s" % HOSTS_URL)
		to_download = True
	else:
		print("* Found old host database, checking age...")
		
		if check_age(HOSTS_FILENAME, DATABASE_AGE):
			print("-> Host database too old, removing")
			os.remove(HOSTS_FILENAME)
			to_download = True
		else:
			print("-> Host database is less than %d days old, reusing." % DATABASE_AGE)
		
	if to_download:
		print("* Downloading host database from %s" % HOSTS_URL)
		hosts_file = urllib.URLopener()
		hosts_file.retrieve(HOSTS_URL, HOSTS_FILENAME)
else:
	if not os.path.isfile(HOSTS_FILENAME):
		print("* Hosts database not found, bailing out.")
		sys.exit(0)
	else:
		print("* Hosts database found, resuming operation...")

# read the source file. Bail out if file isn't there
source_file_exists = False
content = []
try:
	with open(HOSTS_FILENAME) as f:
		f_cont = f.readlines()
		
		f_size = len(f_cont)
		f = 1.0

		for z in f_cont:
			if not z.startswith("#"):
				zz = z.rstrip("\n").split(",")
				zz[1] = zz[1].strip()
				content.append(zz)
			
			f_perc = round(f/f_size, 2)
			update_progress("Generating host list", f_perc)
			
			f+=1
		
		source_file_exists = True
except:
	print("Error reading %s: %s" % (HOSTS_FILENAME, sys.exc_info()[0]))
	raise

# everything we do now, do only if source_file_exists is True:
if source_file_exists and len(content) > 0:
	# check if TARGET_FILE exists, and remove if there
	if os.path.isfile(TARGET_FILE):
		print("Old TARGET_FILE detected, removing...")
		os.remove(TARGET_FILE)

	# start reading  and downloading hosts
	c = 1.0;
	url_count = len(content)
	
	print("There are %d lists in %s" % (url_count, HOSTS_FILENAME))
	
	# check if cache path exists.
	if not os.path.isdir(CACHE_PATH):
		print("* Couldn't find cache directory, creating.")
		os.mkdir(CACHE_PATH)
		
	for url in content:
		try:
			c_perc = c/url_count
			update_progress("Downloading data from %s" % url[1], c_perc)
			
			path = "%s/%s" % (CACHE_PATH, url[1])
			
			if check_age(path, CACHE_AGE):
				downloaded_file = urllib.URLopener()
				downloaded_file.retrieve(str(url[0]), path)
			
			c+=1
		except Exception as e:
			print("Failed to fetch data from %s: %s" % (url[1], repr(e)))
	
	update_progress("Finished downloading data", 1)
	
	# start merging source files and removing them after
	d = 0
	print("* Processing sources and writing to %s" % TARGET_FILE)
	try:
		i = 0
		with open(TARGET_FILE, "w") as target:
			banner = generate_banner()
			target.writelines(banner)
			while d < c:
				try:
					c_url = content[d]
					path = "%s/%s" % (CACHE_PATH, c_url[1])
					with open(path) as source:
						input = source.readlines()
						s_size = len(input)
						j = 1.0
						# sanitize input
						for y in input:
							s_perc = j/s_size
							update_progress("Processing %s" % c_url[1].strip(), s_perc)
							
							y = y.strip()
							y = y.strip("\n")
							if len(y) > 0:
								if not y.startswith(("#", ".", "-", "/", "!", "?", "^", "$", "*", "|", "@", "&", "_", "[", ":", ";", "=", " ", "\r", "\n")):
									if "#" not in y:
										w = y.split()
										
										nline = None
										
										if len(w) > 1:
											nline = "127.0.0.1 %s\n" % w[1]
										elif len(w) == 1:
											nline = "127.0.0.1 %s\n" % w[0]
										else:
											nline = None
											
										# write only if nline is initialised
										if nline != None:
											target.writelines(nline)
											i+=1
								
							j+=1
							
					# remove tmp file
					if not USE_CACHE:
						os.remove(path)
				
				except Exception, err:
					print("Failed reading data from %s: %s" % (str(c_url[0]), repr(err)))
				
				d+=1
		
		print("Written %d hosts to %s" % (i, TARGET_FILE))
		target.close()
	except Exception, e:
		print("Failed to write hosts file: %s" % repr(e))
			

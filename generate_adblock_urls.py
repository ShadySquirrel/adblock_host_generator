#!/usr/bin/python2

#  generate_adblock_urls.py
#  
#  Copyright 2017 Shady Squirrel <shady.squirrel@caramail.com>
#
# Licenced under Apache License Version 2.0 

import urllib
import os
import sys
import time
import sh

#################### CONFIGURATION BLOCK #################### 
''' 
Configuration values:

- HOSTS_FILENAME: file with host providers URLs and descriptions
- HOSTS_ONLINE: use online source for host providers file
- HOSTS_URL: self-explainatory, but ok: address of host provides file
- TARGET_FILE: name of file where hosts are written
- DATABASE_AGE: how old can HOSTS_FILENAME file be before we redownload it. Useful only with HOSTS_ONLINE = True. Age is in days.
- USE_CACHE: Self explainatory - cache downloaded host lists, and reuse them if they are under limited age. Age is in days
- CACHE_PATH: where cache is stored
- ONLY_ADD_NEW: this beauty tells this script to use data from old host file and add new entries, not to overwrite it.
- USE_WHITELIST: allows us to whitelist some domains - for example, definitions from ABP lists contain a lot of wildstrings pointing to Google, Facebook and others, so after cleaning, we get whole domains blocked.
- WHITELISTED_DOMAINS: contains whitelisted domains. Too lazy to move to external file
- AUTO_PUSH: automatically pushes TARGET_FILE to preconfigured git repository.
'''
# All about host source and target file
HOSTS_FILENAME = "adblock_list_domains.txt"
HOSTS_ONLINE = True
HOSTS_URL = "https://raw.githubusercontent.com/ShadySquirrel/adblock_host_generator/master/adblock_list_domains.txt"
TARGET_FILE = "generated_hosts.txt"

# database and cache
DATABASE_AGE = 7
USE_CACHE = True
CACHE_AGE = 0.5
CACHE_PATH = "cache"

# misc
ONLY_ADD_NEW = True
AUTO_PUSH = True

# ignored chars. add yours, freely.
ignore_tuple = ("#", "-","+", ".", ",", "/", "!", "?", "^", "$", "*", "|", "@", "&", "_", "[", "]", ":", ";", "=", " ", "\r", "\n", " ")
ignore_host_tuple = ("#","+", ",", "/", "!", "?", "^", "$", "*", "|", "@", "&", "_", "[", "]", ":", ";", "=", " ", "\r", "\n")
ignore_extensions_touple = (".jpg", ".png", ".html", ".htm", ".php", ".gif")

# Whitelisted domains. Use [] list!
WHITELISTED_DOMAINS = [
	# google block. google code not shown because it's dropped.
	"google.com", "plus.google.com", "drive.google.com", "video.google.com", "apis.google.com", "docs.google.com", "keep.google.com", "play.google.com", "youtube.com",
	# facebook block. Possibly more to add but, who cares?
	"facebook.com", 
	# twitter block
	"twitter.com", "platform.twitter.com", "api.twitter.com", "search.twitter.com",
	# amazon block
	"amazon.com",
	# aliexpress, alibaba
	"aliexpress.com", "alibaba.com",
	# yahoo and yahoo companies
	"search.yahoo.com", "music.yahoo.com", "yahoo.com", "mail.yahoo.com", "flickr.com",
	# microsoft
	"microsoft.com",
	# tumblr
	"tumblr.com", "assets.tumblr.com", "platform.tumblr.com", "static.tumblr.com", 
	# imgur, reddit
	"imgur.com", "reddit.com"
	 ]

#################### CONFIGURATION BLOCK END #################### 

#################### HERE BE LIONS #################### 
'''
update_progress() : Displays or updates a console progress bar
 
Accepts a float between 0 and 1. Any int will be converted to a float.
- A value under 0 represents a 'halt'.
- A value at 1 or bigger represents 100%

Function taken from https://stackoverflow.com/a/15860757, slightly modified to fit my needs
modifications include support for description text (instead of "Percent" used in original)
and little bit fixed formating (description is fixed-width, making things nicer)
'''
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
    text = "\r{0:100} [{1}] {2}% {3}".format( action, "#"*block + "-"*(barLength-block), round(progress*100,2), status)
    sys.stdout.write(text)
    sys.stdout.flush()

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

# parses sent string and returns value and state
def parse_line(y):
	# this defaults to true. runtime changes to false
	write = True 
	
	try: # chances for errors are slim, but better safe than sorry.
		# some lists have specific rules beggining with ||, filter them out. 
		if y.startswith("||"):
			# this should be done bit better?
			y = y.strip("||") 
			z1 = y.split("^") 
			z = z1[0]
			# now split on backslashes, and use only first part of it
			w = z.split("/", 1)
			y = w[0].strip()
		
		# specifics cleaned, now do standard checks. First, check if host entry is valid
		if y.startswith(ignore_tuple): 
			write = False
		
		# check if host is valid - if hosts contains any of symbols from list, ignore it. 
		for sym in ignore_host_tuple: 
			if sym in y: 
				write = False  
		
		# check for file extensions. we're blocking domains, not specific files 
		if y.endswith(ignore_extensions_touple): 
			write = False
		
		# check if host entry is ending in any of those ignored stuffs.
		if y.endswith(ignore_tuple):
			write = False
			
		# check if host is in WHITELISTED_HOSTS:
		if y in WHITELISTED_DOMAINS:
			write = False
	
	except Exception, exc:
		print "ERROR: parsing failed: %s" % str(exc)
		write = False
	
	# all fine, return
	return (write, y)

# reads old hosts file and returns a list of hosts
def read_old_hosts():
	old_hosts = []
	lines = []
	with open(TARGET_FILE, "r") as target:
		lines = target.readlines()
		target.close()
		
	for x in lines:
		if not x.startswith("#"):
			z = x.strip()
			z1 = z.rstrip("\n")
			z2 = z1.rstrip("\r")

			old_hosts.append(z2)
	
	return old_hosts

def find_new_hosts(old, new):
	missing_hosts = []
	# long loop, needs progress
	i = 1.0
	t = float(len(new))
	
	for host in new:
		
		prog = i/t
		if not host.startswith("#"):		
			# clean before testing
			host = host.strip()
			host = host.strip("\n")
			host = host.strip("\r")
					
			if host not in old:
				#print("* Missing %s. appending" % host)
				missing_hosts.append(host)
				
		update_progress("Searching for new entries...", prog)
		i+=1
	
	# finished. return
	return list(set(missing_hosts))
				

# generates banner placed on top of generated hosts file
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
	try:
		# let's assume we don't have to download it
		to_download = False
		
		# check for host database existence
		if not os.path.isfile(HOSTS_FILENAME):
			print("* Downloading host list base from %s" % HOSTS_URL)
			to_download = True
		else:
			print("* Checking age of host list base")
			
			# now, check for database age. 
			# Possible scenario: I've changed something on Linux and uploaded,
			#	but for some sick reason, I'm building file on windows...
			if check_age(HOSTS_FILENAME, DATABASE_AGE):
				print("-> Host list base is older than %d days, redownloading" % DATABASE_AGE)
				os.remove(HOSTS_FILENAME)
				to_download = True
			else:
				print("-> Host list base is still fresh enough")
		
		# to_download flag is true, well, download now. Only reason why I've put try-except here
		if to_download:
			print("* Started host base download.")
			hosts_file = urllib.URLopener()
			hosts_file.retrieve(HOSTS_URL, HOSTS_FILENAME)
	
	except Exception, err:
		print("!! Host database download failed (%s), aborting" % str(err))
		sys.exit(0)
else:
	# this is for good old analogue access - all files on drives, 
	# and when something is missing? blame user.
	if not os.path.isfile(HOSTS_FILENAME):
		print("!! Hosts database not found, bailing out.")
		sys.exit(0)
	else:
		print("* Hosts database found, resuming operation...")

# read the source file. Bail out if file isn't there
# again try-except, because it can fail, miserably.
source_file_exists = False
content = []
try:
	with open(HOSTS_FILENAME) as f:
		f_cont = f.readlines()
		
		f_size = len(f_cont)
		f = 1.0

		for z in f_cont:
			if not z.startswith(ignore_tuple):
				zz = z.rstrip("\n").split(",")
				zz[1] = zz[1].strip()
				content.append(zz)
			
			f_perc = round(f/f_size, 2)
			update_progress("Preparing host list base", f_perc)
			
			f+=1
		
		source_file_exists = True
except:
	print("!! Error reading %s: %s" % (HOSTS_FILENAME, sys.exc_info()[0]))
	raise

# store old hosts here. leave it uninitialized because it maybe won't be even used
old_hosts = []

# everything we do now, do only if source_file_exists is True:
if source_file_exists and len(content) > 0:
	# check if TARGET_FILE exists, and remove if it's there
	if os.path.isfile(TARGET_FILE):
		if not ONLY_ADD_NEW:
			print("* Found old output, removing file.")
			os.remove(TARGET_FILE)
		else:
			print("* Old output found, reusing since ONLY_ADD_NEW flag is set.")

	# start reading  and downloading hosts
	c = 1.0;
	url_count = len(content)
	
	# inform user about everything
	print("* Found %d lists in database." % url_count)
	
	# check if cache path exists.
	if not os.path.isdir(CACHE_PATH):
		print("*! Couldn't find cache directory, creating.")
		os.mkdir(CACHE_PATH)
	
	# download host sources. This should probably be moved to a function.
	dl_succ = False
	for url in content:
		try:
			c_perc = c/url_count
			update_progress("Downloading data from %s" % url[1], c_perc)
			
			path = "%s/%s" % (CACHE_PATH, url[1])
			
			if check_age(path, CACHE_AGE):
				downloaded_file = urllib.URLopener()
				downloaded_file.retrieve(str(url[0]), path)
			
			c+=1
			dl_succ = True
		except Exception as e:
			print("!! Failed to fetch data from %s: %s" % (url[1], repr(e)))
			# not sure if I should bail here or not?
	
	# yeah, we're bailing out like there is no tomorrow.
	if dl_succ:
		print("* Finished downloading data")
	else:
		print "!! Couldn't download host sources, bailing out"
		sys.exit(0)
	
	# start merging source files and removing them after
	d = 0
	print("* Processing sources...")
	
	# this, ladies and gentleman, is our main container for hosts
	# damn python, I can't remember how's this thing called. Touple? Array? Fuck it.
	# we aren't initializing it with existing data in case ONLY_ADD_NEW is true simply because performance impact is, whoh, great.
	hosts = []

	# Now, let's loop!
	while d < url_count:
		try:
			# content[] actually contains host url and file name.
			# file name is used to read data from cache.
			# smart, eh?
			c_url = content[d]
			path = "%s/%s" % (CACHE_PATH, c_url[1])
			
			# open host source file and read it, determine it's size, strip it and parse it
			with open(path) as source:
				input_line = source.readlines()
				s_size = len(input_line)
				
				# this is for progress bar.
				j = 1.0

				try:
					# go line per line and parse.
					for y in input_line:
						s_perc = j/s_size
						update_progress("Parsing list: %s" % c_url[1].strip(), s_perc)
						
						# strip it naked before parsing.
						w = y.strip()
						w = w.strip("\n")
						w = w.strip("\r")						
						y = w
						
						# line is useful to us only if it's longer than 0 chars
						if len(y) > 0:
							# parse, get response and value.
							(write, y) = parse_line(y)
							
							# if response is right, write
							if write:								
								nline = None
								
								# we're dropping the IP part of host, if any.
								w = y.split()
								
								if len(w) > 1:
									nline = "127.0.0.1 %s" % w[1] # see why?
								elif len(w) == 1:
									nline = "127.0.0.1 %s" % w[0]
										
								# write only if nline is initialised
								if nline != None:
										hosts.append(nline)

						# and increment percentage, rinse-repeat.
						j+=1

				except Exception, drnd:
					print("!! Failed  processing entry %s: %s" % (str(y), repr(drnd)))
							
				# remove tmp file
				if not USE_CACHE:
					os.remove(path)
			
		except Exception, err:
			print("!! Failed reading data from %s: %s" % (str(c_url[1]), repr(err)))	

		d+=1
		
	# now, let's write!
	try:
		# initialise to_write as empty list
		to_write = []
		
		# tmp will store our new host values until we decide what to do
		# it also useset set(), because we need to drop duplicates. Sweet, eh?
		tmp = set(hosts)
		
		# now, do a block for ONLY_ADD_NEW and only in case TARGET_FILE EXISTS!
		if ONLY_ADD_NEW and os.path.exists(TARGET_FILE):
			# total old hosts
			old_hosts = read_old_hosts()		
			old_hosts_count = len(old_hosts)
			print("* Old host definitions: %d hosts" % old_hosts_count)
		
			new_host_count = len(tmp)
			print("* New host definitions: %d hosts" % new_host_count)
		
			diff = abs(new_host_count - old_hosts_count)
			if diff > 0:
				print("* Difference is %d hosts" % diff)
			else:
				print("* No difference in sizes. Still rechecking.")
		
			# determine how many hosts are missing - this is a bit long operation,
			# we're talking about 40+k lines, so move to function and show progress
			# AND DO THIS NO MATTER HOW MUCH diff IS. 
			# Simply because we can have it 0, and still get new updates
			missing_hosts = find_new_hosts(old_hosts, tmp)			
			
			# count 'em and show info
			missing_hosts_c = len(missing_hosts)
					
			# inform user and extend current host list
			if missing_hosts_c > 0:
				print("* Appending %d hosts to existing list" % missing_hosts_c)
				old_hosts.extend(list(missing_hosts))
					
				to_write = list(old_hosts)
			else:
				print("* Nothing found, not updating file.")
				
		# because TARGET_FILE doesn't exist or ONLY_ADD_NEW isn't set, fail to default behaviour
		else:
			to_write = list(tmp)
		
		# finally, total number of hosts to write.
		total_hosts = len(to_write)
		
		# count 'em
		cnt = 1.0
		
		if total_hosts > 0:
			# if ONLY_ADD_NEW flag is set, remove old file before writing, and do it silently.
			if ONLY_ADD_NEW and os.path.exists(TARGET_FILE):
				os.remove(TARGET_FILE)
				
			with open(TARGET_FILE, "w") as target:
				# generates banner at the top of file. Contains info about hosts and creation date.
				banner = generate_banner()
				target.writelines(banner)
							
				# now write line by line. Can't be converted to oneliner :(
				for h in to_write:
					nl = "%s\n" % h
					target.writelines(nl)
					
					# calulate percentage
					s_perc = cnt/total_hosts
					
					# inform
					update_progress("Writing hosts %d of %d" % (cnt, total_hosts), s_perc)
					# ++
					cnt+=1
					
				print("* Written %d hosts to %s" % (cnt, TARGET_FILE))
				
				target.close()
				
				# file written an saved, now it's time to push it to git
				if AUTO_PUSH:
					# initialize git via sh module. Smart, eh?
					git = sh.git.bake(_cwd=os.getcwd())
					print("* Initialized git in %s" % os.getcwd())
					
					# generate commit msg
					commit_date = time.strftime("%d.%m.%Y")
					commit_msg = "HOSTS: %s update (%d hosts)" % (commit_date, total_hosts)
					print("* Generated commit message: %s" % commit_msg)
										
					# get remote url
					print("* Generating git url")
					remote = git.remote().strip()
					remote_url = git.remote("get-url", remote, "--push")
					
					# we'll need this later.
					url = remote_url
					
					# grab username and password from config
					from git_config import git_config
					
					# if git is using https instead of ssh, generate push url.
					if git_config["https"]:
						print("* Using HTTPS. Generating push url...")
						
						tmp = remote_url.split("//")
						login_data = "%s:%s" % (git_config["username"], git_config["password"])
						url = "%s//%s@%s" % (tmp[0].strip(), login_data, tmp[1].strip()) # no need for ':', it's left there from spliting.
					
					# add changes
					git.add(TARGET_FILE)
					print("* Adding changes..")
					
					# commit changes
					git.commit(m=commit_msg)
					print("* Commiting changes...")
					
					# push changes
					print("* Pushing changes...")
					git.push(url)
					
					print("* Done!")
		else:
			print("* No changes. You're up to date!")

	except Exception, e:
		print("!! Failed to write hosts file: %s" % repr(e))

#################### NO MORE LIONS :( #################### 

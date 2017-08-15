# Adblock host generator

This is a simple, yet powerfull and configurable Python script which can be used to generate hostlists for ad-blockers (like AdAway for Android, uBlock and AdBlockPlus on Windows, Linux and MacOS) or for personal hosts file on your PC/Mac (just don't forget to add localhost there, haha).

Script is published under Apache License 2.0. See more under [LICENSE](LICENCE).

You can download full hosts file from [here](https://raw.githubusercontent.com/ShadySquirrel/adblock_host_generator/master/out/hostlist.txt).

### Configuration
All customisable and configurable values are stored under CONFIGURATION BLOCK in generate_adblock_urls.py.
Options are:

| Variable | Default value | Description |
|:----------:|:--------------:|:------------|
| `HOSTS_FILENAME` | sources/adblock_list_domains.txt | File containing host provider's URLs and descriptions |
| `HOSTS_ONLINE`|  `True` | Determines if online hosts source file is used, or local one|
| `HOSTS_URL` |  Points to file in this repo | URL where online hosts source is stored |
| `TARGET_FILE` |  out/hostlist.txt | Name of output hosts file |
| `DATABASE_AGE` |  7 | Now old can HOSTS_FILENAME file be before we redownload it. Useful only with HOSTS_ONLINE = True. Age is in days, can be decimal. |
| `USE_CACHE` | `True` | Cache downloaded host definitions, and reuse them if they are under limited age. |
| `CACHE_AGE` |  1 | How long to keep cached definitions stored. Age is in days, can be decimal |
| `CACHE_PATH` |  cache | Path where cached host definitions are stored |
| `ONLY_ADD_NEW` |  `True` | If enabled, only new/non-existing entries to TARGET_FILE are written |
| `USE_WHITELIST` |  `True` | Enables domain whitelisting - needed to keep some sites/apps (like FB, Twitter etc) working. Implemented because of ABP's definitions. |
| `WHITELISTED_DOMAINS` |  `[]` | Contains whitelisted domains. Will probably move to external file one day |
| `WHITELISTED_WILDCARD_DOMAINS` |  `[]` | Same as WHITELISTED_DOMAINS, just for wildstrings. |
| `AUTO_PUSH` |  `True` |  Automatically pushes TARGET_FILE to preconfigured git repository. |

### Command-line arguments
Script supports some of command-line arguments. Those can be useful if you're changing something in the script or just want to generate something different from current file configuration.

Current set of commands is limited, but probably more will come soon, so don't forget to check ocasionally using `-h` argument, if README file isn't updated.

Current set of command-line arguments:

| Argument | Description |
|:-------|:-----------|
| -cc<br>--clear-cache | Clears current cache - removes folder and files in it |
|	-r<br> -- remove| Removes currently generated file |
| -dh<br>--download-hosts	| (Re)downloads host definitions file. Removes cache automatically. |
|	--no-push	| Don't push changes to Git. Commit is still created. |
|	--no-commit	| Disables Git support completely. |

## Issues, requests, contact
Please use GitHub's Issues for any requests, improvements, error reporting and such. Feel free to fork and send merge requests, I never had merge request before. Just respect my ownership over original work.

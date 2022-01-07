## Workshop Collection Downloader

Uses https://steamworkshopdownloader.io/ to download each mod in collection one by one, and save it to one directory. 

### Usage

`python3 wcd.py -cu COLLECTIONURL`

All options `python3 wcd.py -h`:
```
usage: wcd.py [-h] -cu COLLECTIONURL [-dir DIRECTORY] [-f]

optional arguments:
  -h, --help            show this help message and exit
  -cu COLLECTIONURL, --collectionUrl COLLECTIONURL
                        Steam collection url. Pattern: https://steamcommunity.com/workshop/filedetails/?id=*
  -dir DIRECTORY, --directory DIRECTORY
                        Output directory. A folder with collection name will be saved here.
  -f, --force           Do not skip downloaded mods and redownload them.
```

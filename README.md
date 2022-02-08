## Workshop Collection Downloader

Uses https://steamworkshopdownloader.io/ to download each mod in collection one by one, and save it to output directory. 

### Usage

Download collection for the first time: `python3 wcd.py -curl COLLECTIONURL -o OUTPUTFOLDER`
Update collection: `python3 wcd.py -cjson OUTPUTFOLDER/my-collection-name/collection.json`

All options `python3 wcd.py -h`:
```
usage: wcd.py [-h] (-curl COLLECTIONURL | -cjson COLLECTIONJSON) [-o OUTPUT] [-f]

optional arguments:
  -h, --help            show this help message and exit
  -curl COLLECTIONURL, --collectionUrl COLLECTIONURL
                        Steam collection url. Pattern: https://steamcommunity.com/sharedfiles/filedetails/?id=*
  -cjson COLLECTIONJSON, --collectionJson COLLECTIONJSON
                        Generated JSON file from this script.
  -o OUTPUT, --output OUTPUT
                        Output directory. A folder with collection name will be created here.
```

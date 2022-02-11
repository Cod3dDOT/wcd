## Workshop Collection Downloader

#### How to download?
`python3 wcd.py -curl COLLECTIONURL -o OUTPUTFOLDER`

What the script does:
1. Retrieves information about collection from steam api.
2. Saves items in workshop collection to a collection.json file.
3. Uses https://steamworkshopdownloader.io/ to download each item in collection, and save them to output directory.

#### How to update?
`python3 wcd.py -cjson OUTPUTFOLDER/my-collection-name/collection.json`

What the script does:
1. Retrieves information about items in collection.json file from steam api.
2. Compares lastUpdated field for each item in collection.json with steam api response.
3. Uses https://steamworkshopdownloader.io/ to download each item in collection, where lastUpdated does not match the lastest update date.
4. Updates collection.json file with corresponding changes.

#### Does it work if I modify a collection.json file?
Yes, you can modify or create your own collection.json files, and then use them to download / update.
The script will download any items, which are specified in collection.json file.

#### Color coding
When downloading, downloaded items can be of different colors:

- ![#The default color: Item is downloading](https://via.placeholder.com/15/fff/000000?text=+) Default color: Item is downloading
- ![#Yellow color: Item is skipped due to being up-to-date](https://via.placeholder.com/15/ffbc0a/000000?text=+) Yellow color: Item is skipped due to being up-to-date
- ![#Red color: Item is skipped due to error](https://via.placeholder.com/15/d80032/000000?text=+) Red color: Item is skipped due to error

### Options
`python3 wcd.py -h`:
```
usage: wcd.py [-h] (-curl COLLECTIONURL | -cjson COLLECTIONJSON) [-o OUTPUT] [-f]

optional arguments:
  -h, --help            show this help message and exit
  -curl COLLECTIONURL, --collectionUrl COLLECTIONURL
                        Steam collection url. Pattern: https://steamcommunity.com/sharedfiles/filedetails/?id=*
  -cjson COLLECTIONJSON, --collectionJson COLLECTIONJSON
                        Generated collection.json file from this script.
  -o OUTPUT, --output OUTPUT
                        Output directory. A folder with collection name will be saved here.
  -f, --force           Force to redownload everything xD.
```

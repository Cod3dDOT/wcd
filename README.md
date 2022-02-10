## Workshop Collection Downloader

#### How to download?
`python3 wcd.py -curl COLLECTIONURL -o OUTPUTFOLDER`

What the script does:
1. Retrieves information about collection from steam api.
2. Saves items in workshop collection to a .json file.
3. Uses https://steamworkshopdownloader.io/ to download each item in collection one by one, and save it to output directory.

#### How to update?
`python3 wcd.py -cjson OUTPUTFOLDER/my-collection-name/collection.json`

What the script does:
1. Retrieves information about items in .json file from steam api.
2. Compares lastUpdated field for items in json with steam api response.
3. Uses https://steamworkshopdownloader.io/ to download each item in collection, where lastUpdated does not match the lastest update date.
4. Updates .json file with corresponding changes.

#### Does it work if I modify a .json file?
Yes, you can modify or create your own .json files, and then specify them like in 'How to update?' section.
The script will download any items, which are specified in .json file.

#### Color coding
When downloading, downloaded items can be of different colors:

<span style="color:black">The default color (white): Item is downloading</span>
<span style="color:orange">Yellow color: </span>Item is skipped due to being up-to-date
<span style="color:red">Red color: </span>Item is skipped due to error

### Options
`python3 wcd.py -h`:
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

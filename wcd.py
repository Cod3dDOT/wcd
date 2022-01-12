from workshopCollection import WorkshopCollection
import argparse
import os
import json


def parseArgs():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-cu",
                       "--collectionUrl",
                       type=str,
                       help="Steam collection url. Pattern: https://steamcommunity.com/workshop/filedetails/?id=*")

    group.add_argument("-cjson",
                       "--collectionJson",
                       type=str,
                       help="Generated JSON file from this script.")

    parser.add_argument("-dir",
                        "--directory",
                        type=str,
                        required=False,
                        default="downloads/",
                        help="Output directory. A folder with collection name will be saved here.")

    parser.add_argument("-f", "--force",
                        required=False,
                        action="store_true",
                        help="Do not skip downloaded mods and redownload them.")

    args = parser.parse_args()
    return args


def readJsonFile(jsonoFilePath):
    with open(jsonoFilePath, "r") as jsonFile:
        return json.load(jsonFile)


def main():
    args = parseArgs()
    dir = os.path.abspath(args.directory)
    force = args.force

    steamUrl = args.collectionUrl
    jsonPath = args.collectionJson

    wCollection = None
    if (steamUrl):
        wCollection = WorkshopCollection.fromUrl(steamUrl)

    if (jsonPath):
        jsonDict = readJsonFile(jsonPath)
        wCollection = WorkshopCollection.fromJson(jsonDict)
    wCollection.download(dir, force)


if __name__ == "__main__":
    main()

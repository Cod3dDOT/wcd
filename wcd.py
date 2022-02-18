# 1.1.3

import argparse
import os
import json

from classes import WorkshopCollection
from api import SteamDownloaderAPI
from utils import logger


def parseArgs():
    parser = argparse.ArgumentParser()

    source = parser.add_mutually_exclusive_group(required=True)

    source.add_argument("-curl", "--collectionUrl",
                        type=str,
                        help="Steam collection url. Pattern: https://steamcommunity.com/sharedfiles/filedetails/?id=*")

    source.add_argument("-cjson", "--collectionJson",
                        type=str,
                        help="Generated collection.json file from this script.")

    parser.add_argument("-o", "--output",
                        type=str,
                        required=False,
                        default="downloads/",
                        help="Output directory. A folder with collection name will be saved here. Defaults to /downloads/")

    parser.add_argument("-f", "--force",
                        required=False,
                        action="store_true",
                        help="Force redownload everything. (only when updating)")

    parser.add_argument("-c", "--cleanUp",
                        required=False,
                        action="store_true",
                        help="Clean up removed items. (only when updating)")

    args = parser.parse_args()

    directory = os.path.abspath(args.output)
    force = args.force
    cleanUp = args.cleanUp

    steamUrl = args.collectionUrl
    jsonPath = args.collectionJson

    return directory, force, steamUrl, jsonPath, cleanUp


def readJsonFile(jsonPath):
    with open(jsonPath, "r") as jsonFile:
        return json.load(jsonFile)


def main():
    OutputDirectory, ForceRedownload, \
        SteamCollectionUrl, JsonFilePath, CleanUp = parseArgs()

    wCollection = None
    if (SteamCollectionUrl):
        wCollection = WorkshopCollection.fromUrl(SteamCollectionUrl)

    if (JsonFilePath):
        jsonDict = readJsonFile(JsonFilePath)
        wCollection = WorkshopCollection.fromJson(jsonDict)

    if (not wCollection):
        logger.LogError("Could not create collection.")
        return

    try:
        result = wCollection.FetchNewItems()
        if (not result):
            logger.LogError(
                f"Could not fetch any items for collection: {wCollection}"
            )
        if (SteamCollectionUrl or ForceRedownload):
            SteamDownloaderAPI.DownloadCollection(
                wCollection, OutputDirectory, True
            )
        else:
            SteamDownloaderAPI.UpdateCollection(
                wCollection, OutputDirectory, True, CleanUp
            )
    except KeyboardInterrupt:
        SteamDownloaderAPI.StopDownload()


if (__name__ == "__main__"):
    main()

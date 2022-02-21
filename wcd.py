# 1.1.4

import argparse
import os
import json

from classes import WorkshopCollection
from classes.workshopCollection import WorkshopCollectionException
from api import SteamDownloaderAPI
from utils import logger


def parseArgs():
    parser = argparse.ArgumentParser()

    source = parser.add_mutually_exclusive_group(required=True)

    source.add_argument("-curl", "--collectionUrl",
                        type=str,
                        help="Steam collection url. "
                        "Pattern: https://steamcommunity.com/(sharedfiles | workshop)/filedetails/?id=*")

    source.add_argument("-cjson", "--collectionJson",
                        type=str,
                        help="Generated collection.json")

    parser.add_argument("-o", "--output",
                        type=str,
                        required=False,
                        default="downloads/",
                        help="Output directory. "
                        "A folder with collection name will be saved here. "
                        "Defaults to /downloads/")

    parser.add_argument("-f", "--force",
                        required=False,
                        action="store_true",
                        help="Force redownload. (only when updating)")

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
        try:
            wCollection = WorkshopCollection.fromUrl(SteamCollectionUrl)
        except WorkshopCollectionException:
            logger.LogError(
                "Could not create collection."
            )
            return

    if (JsonFilePath):
        jsonDict = readJsonFile(JsonFilePath)
        try:
            wCollection = WorkshopCollection.fromJson(jsonDict)
        except WorkshopCollectionException:
            logger.LogError(
                "Could not create collection."
            )
            return

    try:
        try:
            wCollection.FetchNewItems()
        except WorkshopCollectionException as exception:
            logger.LogError(exception)
            return

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

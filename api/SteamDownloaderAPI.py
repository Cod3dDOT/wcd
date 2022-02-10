import json
import requests
import io
import time

from classes import WorkshopCollection
from classes import WorkshopItem

from utils import logger
from api import SteamAPI

isDownloading = False
stopDownload = False


def StopDownload():
    global stopDownload

    if (isDownloading):
        logger.LogWarning(
            f"{logger.StartIndent()}Stopping download..."
        )
        stopDownload = True


def DownloadCollection(collection: WorkshopCollection, directory: str, forceRedownload: bool = False) -> None:
    '''Downloads all mods in collection.\n
    WARNING: collections maybe very big, so this command may generate a lot of internet traffic and take a while.'''

    global isDownloading
    global stopDownload

    hasValidId = SteamAPI.Validator.ValidSteamItemId(collection.id) or \
        collection.id == "DummyIdForLocalCollection"

    hasValidAppId = SteamAPI.Validator.ValidSteamItemId(collection.appid)

    if (not hasValidId or not hasValidAppId):
        logger.LogError(
            f"{logger.StartIndent()}Can't download collection without knowing its id or its app id.\n"
            f"{logger.Indent(1)}Call SteamApi.getCollectionDetails() first!\n"
            f"{logger.Indent(1)}Called with collection: {collection}"
        )
        return

    hasItemsToDownload = len([
        item for item
        in collection.items
        if item.needsUpdate == True
    ]) > 0 or forceRedownload

    if (not hasItemsToDownload):
        logger.LogError(
            f"{logger.StartIndent()}Collection has no items to download.\n"
            f"{logger.Indent(1)}Called with collection: {collection}"
        )
        return

    logger.LogMessage(
        f"{logger.StartIndent()}"
        f"Downloading collection: {collection.name}"
    )
    collectionDirectory = f"{directory}/{collection.name}"

    isDownloading = True

    skippedDownloads = 0
    successfulDownloads = 0
    for index, item in enumerate(collection.items):

        itemDirectory = f"{collectionDirectory}/{item.name}"

        download = item.needsUpdate or forceRedownload
        if (not download):
            logger.LogWarning(
                f"{logger.Indent(2)}"
                f"{index}. "
                f"{item.name}"
            )
            skippedDownloads += 1
            continue
        else:
            logger.LogMessage(
                f"{logger.Indent(1)}"
                f"{index}. "
                f"{item.name}"
            )
        try:
            downloadedData = downloadItem(item)
            item.downloadedData = downloadedData
            item.saveToDisk(itemDirectory)
            successfulDownloads += 1
        except Exception as exception:
            logger.LogError(
                f"{logger.StartIndent()}Exception occured while trying to download collection\n"
                f"{logger.Indent(1)}{exception}"
            )
        if (stopDownload):
            logger.LogSuccess(
                f"{logger.StartIndent()}Download stopped"
            )
            isDownloading = False
            stopDownload = False
            return

    collection.saveAsJson(collectionDirectory)

    logger.LogSuccess(
        f"Downloaded collection: {collection.name}. \
        Items: {successfulDownloads}/{len(collection.items)}"
    )


def getSteamDownloaderUrl(item: WorkshopItem):
    requestUrl = "https://node03.steamworkshopdownloader.io/prod/api/download/request"
    requestData = {
        "publishedFileId": item.id,
        "collectionId": None,
        "hidden": False,
        "downloadFormat": "raw",
        "autodownload": False
    }
    requestHeaders = {
        "Content-type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }
    requestResponse = requests.post(
        requestUrl, json=requestData, headers=requestHeaders
    )
    uuid = json.loads(requestResponse.text)["uuid"]
    for _ in range(3):
        time.sleep(2)
        statusUrl = "https://node03.steamworkshopdownloader.io/prod/api/download/status"
        statusData = f'''{{"uuids":["{uuid}"]}}'''
        statusHeaders = {
            "Content-type": "application/json"
        }
        statusResponse = requests.post(
            statusUrl, data=statusData, headers=statusHeaders
        )
        jsonStatusResponse = json.loads(statusResponse.text)[uuid]
        status = jsonStatusResponse["status"]
        if (status == "prepared"):
            storageHost = jsonStatusResponse["storageNode"]
            storagePath = jsonStatusResponse["storagePath"]
            zipFileUrl = f"https://{storageHost}/prod//storage//{storagePath}?uuid={uuid}"
            return zipFileUrl


def getSteamDownloaderCachedUrl(item: WorkshopItem):
    url = "http://steamworkshop.download/online/steamonline.php"
    data = {"item": item.id, "app": item.appid}
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    response = requests.post(
        url, data=data, headers=headers
    )
    if (response.text == "" or response.text == "<pre>Sorry, this file is not available. Need re-download.</pre>"):
        logger.LogError(
            f"{logger.Indent(3)}Error downloading. Please try ot download this item manually."
        )
        return
    zipFileUrl = response.text.split("<a href='")[1].split("'>")[0]
    return zipFileUrl


def downloadItem(item: WorkshopItem):
    '''Downloads item.'''

    if (not SteamAPI.Validator.ValidSteamItemId(item.id) or
            not SteamAPI.Validator.ValidSteamItemId(item.appid)
        ):
        raise Exception(
            "Can't download item without knowing its id or its app id."
        )

    zipFileUrl = getSteamDownloaderUrl(item)
    if (not zipFileUrl):
        logger.LogError(
            f"{logger.Indent(3)}Error downloading. Please try ot download this item manually."
        )
        return

    with io.BytesIO() as memoryFile:
        downloadResponse = requests.get(zipFileUrl, stream=True)
        totalLength = downloadResponse.headers.get('content-length')
        downloadedBytesSize = 0
        if totalLength is None:
            memoryFile.write(downloadResponse.content)
            logger.LogWarning(
                f"{logger.Indent(2)}Can't track download progress. Downloading..."
            )
        else:
            for chunk in downloadResponse.iter_content(1024):
                downloadedBytesSize += len(chunk)
                memoryFile.write(chunk)
                done = int(30 * downloadedBytesSize / int(totalLength))
                print(
                    f"{logger.Indent(2)}Downloading [{'=' * done}{' ' * (30-done)}]", end="\r"
                )
        logger.LogMessage("")
        memoryFile.seek(0)
        return memoryFile.read()

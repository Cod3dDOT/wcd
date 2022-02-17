import json
import requests
import io
import time

from classes import WorkshopCollection
from classes import WorkshopItem

from utils import filemanager, logger
from api import SteamAPI


_ongoingDownload: WorkshopCollection = None
_ongoingDownloadSaveDirectory: str = None
_ongoingDownloadDownloadedItems: list[WorkshopItem] = []


def IsDownloading() -> bool:
    return _ongoingDownload != None


def OngoingDownload() -> WorkshopCollection:
    return _ongoingDownload


def StopDownload():
    global _ongoingDownload
    global _ongoingDownloadDownloadedItems
    global _ongoingDownloadSaveDirectory

    if IsDownloading():
        logger.LogWarning(
            f"{logger.StartIndent()}Stopping download..."
        )

        downloadedIds = WorkshopCollection.getItemIds(
            _ongoingDownloadDownloadedItems
        )
        # add not downloaded items with lastUpdated = 0,
        # so thay will be "updated" the next time.
        for item in _ongoingDownload.fetchedItems:
            if item.id not in downloadedIds:
                item.lastUpdated = 0
                _ongoingDownloadDownloadedItems.append(item)

        filemanager.saveCollectionAsJson(
            _ongoingDownload, _ongoingDownloadDownloadedItems, _ongoingDownloadSaveDirectory
        )

        _ongoingDownload = None
        _ongoingDownloadSaveDirectory = None
        _ongoingDownloadDownloadedItems = []


def UpdateCollection(collection: WorkshopCollection, directory: str, removeOldItems: bool = True, removeDeletedItems: bool = True) -> None:
    '''Checks all items in collection, and updates/adds/removes them as needed\n
    WARNING: collections maybe very big, so this command may generate a lot of internet traffic and take a while.'''
    global _ongoingDownloadSaveDirectory
    _ongoingDownloadSaveDirectory = f"{directory}/{collection.name}"
    global _ongoingDownload
    _ongoingDownload = collection

    # Fetched items info
    fetchedItemIdsList: list[int] = WorkshopCollection.getItemIds(
        collection.fetchedItems
    )
    fetchedItemIdsSet: set[int] = set(fetchedItemIdsList)
    fetchedItemsNameList: list[str] = WorkshopCollection.getItemNames(
        collection.fetchedItems
    )

    # Local items info
    localItemIdsList: list[int] = WorkshopCollection.getItemIds(
        collection.localItems
    )
    localItemIdsSet: set[int] = set(localItemIdsList)

    # Will be downloaded
    willBeAddedIds: list[int] = list(
        fetchedItemIdsSet - localItemIdsSet
    )

    # Will be deleted
    willBeDeletedIds: list[int] = set(
        localItemIdsSet - fetchedItemIdsSet
    )

    # Will be updated
    willBeUpdatedIds: list[int] = list(
        item.id for item
        in collection.localItems
        if item.lastUpdated != collection.fetchedItems[
            fetchedItemIdsList.index(item.id)
        ].lastUpdated
    )

    # Will be skipped (they are up to date)
    willBeIgnoredIds: list[int] = list(
        (fetchedItemIdsSet - set(willBeUpdatedIds)) - set(willBeAddedIds)
    )

    # These are different from line 50.
    # If you manually remove items from collection.json,
    # then we do not longer have any info about them. So we scan for all folders,
    # and delete all folders that are not in names list (folders are named using item names)
    willBeDeletedFolders: list[str] = list(
        dir for dir
        in filemanager.listDirsInDirectory(_ongoingDownloadSaveDirectory)
        if (dir not in fetchedItemsNameList)
    )

    if (len(willBeUpdatedIds) == 0 and
        len(willBeDeletedIds) == 0 and
        len(willBeAddedIds) == 0 and
        len(willBeDeletedFolders) == 0
        ):
        logger.LogError(
            f"{logger.StartIndent()}Collection has no items to change.\n"
            f"{logger.Indent(1)}Called with collection: {collection}"
        )
        return

    hasValidAppId = SteamAPI.Validator.ValidSteamItemId(collection.appid)

    if (not hasValidAppId):
        logger.LogError(
            f"{logger.StartIndent()}Can't download collection without knowing its id or its app id.\n"
            f"{logger.Indent(1)}Call SteamApi.getCollectionDetails() first!\n"
            f"{logger.Indent(1)}Called with collection: {collection}"
        )
        return

    logger.LogMessage(
        f"{logger.StartIndent()}Updating collection: {collection.name}"
    )

    global _ongoingDownloadDownloadedItems
    _ongoingDownloadDownloadedItems += [
        item for item
        in collection.fetchedItems
        if item.id in willBeIgnoredIds
    ]

    if len(willBeIgnoredIds) > 0:
        logger.LogMessage(
            f"{logger.Indent(1)}Ignoring {len(willBeIgnoredIds)} up to date items"
        )

    if ((len(willBeDeletedIds) > 0 or len(willBeDeletedFolders)) and removeDeletedItems):
        logger.LogMessage(
            f"{logger.Indent(1)}Removing {len(willBeDeletedIds) + len(willBeDeletedFolders)} items"
        )
        for index, itemId in enumerate(willBeDeletedIds):
            itemIndex = localItemIdsList.index(itemId)
            item = collection.localItems[itemIndex]
            logger.LogError(
                f"{logger.Indent(2)}"
                f"{index}. "
                f"{item.name}"
            )
            itemDirectory = f"{_ongoingDownloadSaveDirectory}/{item.name}"
            if (filemanager.doesDirectoryExist(itemDirectory)):
                filemanager.deleteDirectory(itemDirectory)

        for folder in willBeDeletedFolders:
            logger.LogError(
                f"{logger.Indent(2)}"
                f"Deleting folder no longer associated with collection: "
                f"{folder}"
            )
            if (filemanager.doesDirectoryExist(f"{_ongoingDownloadSaveDirectory}/{folder}")):
                filemanager.deleteDirectory(
                    f"{_ongoingDownloadSaveDirectory}/{folder}")

    failedToUpdateIds: list[WorkshopItem] = []
    if len(willBeUpdatedIds) > 0:
        logger.LogMessage(
            f"{logger.Indent(1)}Updating {len(willBeUpdatedIds)} old items"
        )

        for index, itemId in enumerate(willBeUpdatedIds):
            fetchedItemIndex = fetchedItemIdsList.index(itemId)
            fetchedItem = collection.fetchedItems[fetchedItemIndex]
            fetchedItemDirectory = f"{_ongoingDownloadSaveDirectory}/{fetchedItem.name}"

            localItemIndex = localItemIdsList.index(itemId)
            localItem = collection.localItems[localItemIndex]
            localItemDirectory = f"{_ongoingDownloadSaveDirectory}/{localItem.name}"

            logger.LogMessage(
                f"{logger.Indent(1)}"
                f"{index}. "
                f"{fetchedItem.name}"
            )

            if (filemanager.doesDirectoryExist(localItemDirectory) and removeOldItems):
                logger.LogMessage(f"{logger.Indent(2)}Deleting old folder...")
                filemanager.deleteDirectory(localItemDirectory)

            if (filemanager.doesDirectoryExist(fetchedItemDirectory)):
                logger.LogMessage(f"{logger.Indent(2)}Deleting old folder...")
                filemanager.deleteDirectory(fetchedItemDirectory)

            try:
                downloadedData = downloadItem(fetchedItem)
                logger.LogMessage(f"{logger.Indent(2)}Extracting...")
                filemanager.saveZipFile(fetchedItemDirectory, downloadedData)
                # add only when downloaded withoout errors
                _ongoingDownloadDownloadedItems.append(fetchedItem)
            except Exception as exception:
                logger.LogError(
                    f"{logger.Indent(1)}{logger.StartIndent()}Exception occured while trying to download item: \n"
                    f"{logger.Indent(2)}{exception}"
                )
                failedToUpdateIds.append(localItem.id)

    failedToAddIds: list[int] = []
    if len(willBeAddedIds) > 0:
        logger.LogMessage(
            f"{logger.Indent(1)}Downloading {len(willBeAddedIds)} new items"
        )

        for index, itemId in enumerate(willBeAddedIds):
            fetchedItemIndex = fetchedItemIdsList.index(itemId)
            fetchedItem = collection.fetchedItems[fetchedItemIndex]
            fetchedItemDirectory = f"{_ongoingDownloadSaveDirectory}/{fetchedItem.name}"

            logger.LogMessage(
                f"{logger.Indent(1)}"
                f"{index}. "
                f"{fetchedItem.name}"
            )

            try:
                downloadedData = downloadItem(fetchedItem)
                logger.LogMessage(f"{logger.Indent(2)}Extracting...")
                filemanager.saveZipFile(fetchedItemDirectory, downloadedData)
                # add only when downloaded withoout errors
                _ongoingDownloadDownloadedItems.append(fetchedItem)
            except Exception as exception:
                logger.LogError(
                    f"{logger.Indent(1)}{logger.StartIndent()}Exception occured while trying to download item: \n"
                    f"{logger.Indent(2)}{exception}"
                )
                failedToAddIds.append(fetchedItem.id)

    # this ensures we do not update old items which failed to download
    for item in collection.fetchedItems:
        failedToUpdate = item.id in failedToUpdateIds

        if (failedToUpdate):
            # If item failed to update, we get the old info for it
            # So basically we leave it untouched
            localItemIndex = localItemIdsList.index(item.id)
            localItem = collection.localItems[localItemIndex]
            _ongoingDownloadDownloadedItems.append(localItem)

    filemanager.saveCollectionAsJson(
        _ongoingDownload, _ongoingDownloadDownloadedItems, _ongoingDownloadSaveDirectory
    )

    logger.LogSuccess(
        f"{logger.StartIndent()}Updated collection: {collection.name}.\n"
        f"{logger.Indent(1)}Added items: {len(willBeAddedIds) - len(failedToAddIds)}/{len(willBeAddedIds)}\n"
        f"{logger.Indent(1)}Updated items: {len(willBeUpdatedIds) - len(failedToUpdateIds)}/{len(willBeUpdatedIds)}\n"
        f"{logger.Indent(1)}Removed items: {len(willBeDeletedIds) + len(willBeDeletedFolders)}"
    )


def DownloadCollection(collection: WorkshopCollection, directory: str, overrideExistingDirectory: bool = False) -> None:
    '''Downloads all mods in collection.\n
    WARNING: collections maybe very big, so this command may generate a lot of internet traffic and take a while.'''
    global _ongoingDownloadSaveDirectory
    _ongoingDownloadSaveDirectory = f"{directory}/{collection.name}"

    if filemanager.doesDirectoryExist(_ongoingDownloadSaveDirectory):
        if (overrideExistingDirectory):
            filemanager.deleteDirectory(_ongoingDownloadSaveDirectory)
        else:
            logger.LogError(
                f"Directory already exists: {_ongoingDownloadSaveDirectory}")
            return

    if (len(collection.fetchedItems) == 0):
        logger.LogError(
            f"{logger.StartIndent()}Collection has no items to download.\n"
            f"{logger.Indent(1)}Called with collection: {collection}"
        )
        return

    hasValidAppId = SteamAPI.Validator.ValidSteamItemId(collection.appid)

    if (not hasValidAppId):
        logger.LogError(
            f"{logger.StartIndent()}Can't download collection without knowing its app id.\n"
            f"{logger.Indent(1)}Call SteamApi.getCollectionDetails() first!\n"
            f"{logger.Indent(1)}Called with collection: {collection}"
        )
        return

    logger.LogMessage(
        f"{logger.StartIndent()}"
        f"Downloading collection: {collection.name}"
    )

    global _ongoingDownload
    global _ongoingDownloadDownloadedItems
    _ongoingDownload = collection

    logger.LogMessage(
        f"{logger.Indent(1)}Downloading {len(collection.fetchedItems)} items"
    )

    failedDownloadIds: list[int] = []
    for index, item in enumerate(collection.fetchedItems):
        logger.LogMessage(
            f"{logger.Indent(1)}"
            f"{index}. "
            f"{item.name}"
        )
        try:
            downloadedData = downloadItem(item)
            itemDirectory = f"{_ongoingDownloadSaveDirectory}/{item.name}"
            if (filemanager.doesDirectoryExist(itemDirectory)):
                filemanager.deleteDirectory(itemDirectory)
            print(f"{logger.Indent(2)}Extracting...")
            filemanager.saveZipFile(itemDirectory, downloadedData)
            _ongoingDownloadDownloadedItems.append(item)
        except Exception as exception:
            logger.LogError(
                f"{logger.Indent(1)}{logger.StartIndent()}Exception occured while trying to download item: \n"
                f"{logger.Indent(2)}{exception}"
            )
            failedDownloadIds.append(item.id)

    filemanager.saveCollectionAsJson(
        _ongoingDownload, _ongoingDownloadDownloadedItems, _ongoingDownloadSaveDirectory
    )

    logger.LogSuccess(
        f"Downloaded collection: {collection.name}\n"
        f"Downloaded items: {len(_ongoingDownloadDownloadedItems)}/{len(collection.fetchedItems)}"
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


# def getSteamDownloaderCachedUrl(item: WorkshopItem):
#     url = "http://steamworkshop.download/online/steamonline.php"
#     data = {"item": item.id, "app": item.appid}
#     headers = {"Content-type": "application/x-www-form-urlencoded"}
#     response = requests.post(
#         url, data=data, headers=headers
#     )
#     if (response.text == "" or response.text == "<pre>Sorry, this file is not available. Need re-download.</pre>"):
#         logger.LogError(
#             f"{logger.Indent(3)}Error downloading. Please try ot download this item manually."
#         )
#         return
#     zipFileUrl = response.text.split("<a href='")[1].split("'>")[0]
#     return zipFileUrl


def downloadItem(item: WorkshopItem):
    '''Downloads item.'''

    downloadBarLength = 30

    if (not SteamAPI.Validator.ValidSteamItemId(item.id) or
        not SteamAPI.Validator.ValidSteamItemId(item.appid)
        ):
        raise Exception(
            "Can't download item without knowing its id or its app id."
        )

    zipFileUrl = getSteamDownloaderUrl(item)
    if (not zipFileUrl):
        logger.LogError(
            f"{logger.Indent(2)}Error downloading. Please try ot download this item manually."
        )
        return

    with io.BytesIO() as memoryFile:
        downloadResponse = requests.get(zipFileUrl, stream=True)
        totalLength = downloadResponse.headers.get('content-length')
        if totalLength is None:
            memoryFile.write(downloadResponse.content)
            logger.LogWarning(
                f"{logger.Indent(2)}Can't track download progress. Downloading..."
            )
        else:
            print(
                f"{logger.Indent(2)}Downloading [{' ' * downloadBarLength}]", end="\r"
            )
            for chunk in downloadResponse.iter_content(1024):
                memoryFile.write(chunk)
                downloadBarDone = int(
                    downloadBarLength *
                    memoryFile.getbuffer().nbytes / int(totalLength)
                )
                print(
                    f"{logger.Indent(2)}Downloading [{'=' * downloadBarDone}{' ' * (downloadBarLength-downloadBarDone)}]", end="\r"
                )
        logger.LogMessage("")
        memoryFile.seek(0)
        return memoryFile.read()

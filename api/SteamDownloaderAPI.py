import json
from typing import Optional
from zipfile import BadZipFile
import requests
import io
import time

from classes import WorkshopCollection
from classes import WorkshopItem

from utils import AssertParameter, filemanager, logger
from api import SteamAPI


_ongoingDownload: WorkshopCollection = None
_ongoingDownloadSaveDirectory: str = ""
_ongoingDownloadDownloadedItems: list[WorkshopItem] = []


def IsDownloading() -> bool:
    '''Returns True of currently downloading anything'''
    return _ongoingDownload != None


def OngoingDownload() -> Optional[WorkshopCollection]:
    '''Returns collection thta is currently downloaded'''
    return _ongoingDownload


def DownloadedItems() -> list[WorkshopItem]:
    '''Returns items already downloaded'''
    return _ongoingDownloadDownloadedItems


def onDownloadStopped() -> None:
    global _ongoingDownload
    global _ongoingDownloadDownloadedItems
    global _ongoingDownloadSaveDirectory

    _ongoingDownload = None
    _ongoingDownloadSaveDirectory = ""
    _ongoingDownloadDownloadedItems = []


def StopDownload() -> None:
    '''Stops the download'''
    global _ongoingDownload
    global _ongoingDownloadDownloadedItems
    global _ongoingDownloadSaveDirectory

    if (IsDownloading()):
        logger.LogMessage("")
        logger.LogWarning(
            f"{logger.StartIndent()}Stopping download..."
        )

        downloadedIds = WorkshopCollection.getItemIds(
            _ongoingDownloadDownloadedItems
        )
        # add not downloaded items with lastUpdated = 0,
        # so thay will be "updated" the next time.
        for item in _ongoingDownload.fetchedItems:
            if (item.id not in downloadedIds):
                item.lastUpdated = 0
                _ongoingDownloadDownloadedItems.append(item)

        filemanager.saveCollectionAsJson(
            f"{_ongoingDownloadSaveDirectory}/collection.json",
            _ongoingDownload,
            _ongoingDownloadDownloadedItems,
            True
        )

        onDownloadStopped()


def UpdateCollection(collection: WorkshopCollection, directory: str, removeOldItems: bool = True, removeDeletedItems: bool = True) -> None:
    '''Checks all items in collection, and updates/adds/removes them as needed\n
    WARNING: collections maybe very big, so this command may generate a lot of internet traffic and take a while.'''

    if (not isinstance(collection, WorkshopCollection)):
        raise Exception(
            f"collection must be of type {WorkshopCollection}\n"
            f"collection: {collection}, type: {type(collection)}"
        )

    if (not isinstance(directory, str)):
        raise Exception(
            f"directory must be of type {str}\n"
            f"directory: {directory}, type: {type(directory)}"
        )

    if (not collection.name):
        raise Exception("Cant update collection not knowing its name")

    hasValidAppId = SteamAPI.Validator.ValidSteamItemId(collection.appid)
    if (not hasValidAppId):
        logger.LogError(
            f"{logger.StartIndent()}Can't download collection without knowing its id or its app id.\n"
            f"{logger.Indent(1)}Call SteamApi.getCollectionDetails() first!\n"
            f"{logger.Indent(1)}Called with collection: {collection}"
        )
        return

    if (len(collection.fetchedItems) == 0):
        queryResult = logger.YesOrNoQuery(
            "There are no fetched items. This means ALL items will be removed!\nAre you sure you have called WorkshopCollection.FetchNewItems()?",
            False,
            "yes, continue",
            "no, abort!"
        )
        if (not queryResult):
            return

    collectionDirectory = f"{directory}/{collection.name}"

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
    willBeDeletedIdsSet: set[int] = set(
        localItemIdsSet - fetchedItemIdsSet
    )

    # Will be updated
    willBeUpdatedIds: list[int] = list(
        item.id for item
        in collection.localItems
        if item.id in fetchedItemIdsList and
        item.lastUpdated != collection.fetchedItems[
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
        in filemanager.listDirsInDirectory(collectionDirectory)
        if (dir not in fetchedItemsNameList)
    )

    if (len(willBeUpdatedIds) == 0 and
        len(willBeDeletedIdsSet) == 0 and
        len(willBeAddedIds) == 0 and
        len(willBeDeletedFolders) == 0
        ):
        logger.LogError(
            f"{logger.StartIndent()}Collection has no items to change.\n"
            f"{logger.Indent(1)}Called with collection: {collection}"
        )
        return

    logger.LogMessage(
        f"{logger.StartIndent()}Updating collection: {collection.name}"
    )

    global _ongoingDownloadSaveDirectory
    _ongoingDownloadSaveDirectory = collectionDirectory
    global _ongoingDownload
    _ongoingDownload = collection
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

    if ((len(willBeDeletedIdsSet) > 0 or len(willBeDeletedFolders)) and removeDeletedItems):
        logger.LogMessage(
            f"{logger.Indent(1)}Removing {len(willBeDeletedIdsSet) + len(willBeDeletedFolders)} items"
        )
        for index, itemId in enumerate(willBeDeletedIdsSet):
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

    failedToUpdateIds: list[int] = []
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

            downloadedData = None
            try:
                downloadedData = downloadItem(fetchedItem)
            except TimeoutError:
                logger.LogError(
                    f"{logger.Indent(2)}Error occured while trying to download this item."
                )
                failedToUpdateIds.append(fetchedItem.id)
                continue

            logger.LogMessage(f"{logger.Indent(2)}Extracting...")
            try:
                filemanager.saveZipFile(fetchedItemDirectory, downloadedData)
                _ongoingDownloadDownloadedItems.append(fetchedItem)
            except BadZipFile:
                logger.LogError(
                    "Error occured while trying to unzip this item")
                failedToUpdateIds.append(fetchedItem.id)

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

            downloadedData: bytes = None
            try:
                downloadedData = downloadItem(fetchedItem)
            except TimeoutError:
                logger.LogError(
                    f"{logger.Indent(2)}Error occured while trying to download this item."
                )
                failedToAddIds.append(fetchedItem.id)
                continue

            if (filemanager.doesDirectoryExist(fetchedItemDirectory)):
                filemanager.deleteDirectory(fetchedItemDirectory)
            logger.LogMessage(f"{logger.Indent(2)}Extracting...")
            try:
                filemanager.saveZipFile(fetchedItemDirectory, downloadedData)
                _ongoingDownloadDownloadedItems.append(fetchedItem)
            except BadZipFile:
                logger.LogError(
                    "Error occured while trying to unzip this item"
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
        f"{_ongoingDownloadSaveDirectory}/collection.json",
        _ongoingDownload,
        _ongoingDownloadDownloadedItems,
        True
    )
    filemanager.saveCollectionAsJson(
        f"{_ongoingDownloadSaveDirectory}/collection_backup.json",
        _ongoingDownload,
        _ongoingDownload.localItems,
        True
    )

    onDownloadStopped()
    logger.LogSuccess(
        f"{logger.StartIndent()}Updated collection: {collection.name}.\n"
        f"{logger.Indent(1)}Added items: {len(willBeAddedIds) - len(failedToAddIds)}/{len(willBeAddedIds)}\n"
        f"{logger.Indent(1)}Updated items: {len(willBeUpdatedIds) - len(failedToUpdateIds)}/{len(willBeUpdatedIds)}\n"
        f"{logger.Indent(1)}Removed items: {len(willBeDeletedIdsSet) + len(willBeDeletedFolders)}"
    )


def DownloadCollection(collection: WorkshopCollection, directory: str, overrideExistingDirectory: bool = False) -> None:
    '''Downloads all items in collection.\n
    WARNING: collections maybe very big, so this command may generate a lot of internet traffic and take a while.'''

    collectionDirectory = f"{directory}/{collection.name}"

    if (filemanager.doesDirectoryExist(collectionDirectory)):
        if (overrideExistingDirectory):
            filemanager.deleteDirectory(collectionDirectory)
        else:
            logger.LogError(
                f"Directory already exists: {collectionDirectory}")
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
    global _ongoingDownloadSaveDirectory
    _ongoingDownloadSaveDirectory = collectionDirectory
    _ongoingDownload = collection

    logger.LogMessage(
        f"{logger.Indent(1)}Downloading {len(collection.fetchedItems)} items"
    )

    failedDownloadIds: list[int] = []
    for index, item in enumerate(collection.fetchedItems):
        itemDirectory = f"{_ongoingDownloadSaveDirectory}/{item.name}"

        logger.LogMessage(
            f"{logger.Indent(1)}"
            f"{index}. "
            f"{item.name}"
        )

        downloadedData = None
        try:
            downloadedData = downloadItem(item)
        except TimeoutError:
            logger.LogError(
                f"{logger.Indent(2)}Error occured while trying to download this item."
            )
            failedDownloadIds.append(item.id)
            continue

        if (filemanager.doesDirectoryExist(itemDirectory)):
            filemanager.deleteDirectory(itemDirectory)
        logger.LogMessage(f"{logger.Indent(2)}Extracting...")
        try:
            filemanager.saveZipFile(itemDirectory, downloadedData)
            _ongoingDownloadDownloadedItems.append(item)
        except BadZipFile:
            logger.LogError("Error occured while trying to unzip this item")
            failedDownloadIds.append(item.id)

    filemanager.saveCollectionAsJson(
        f"{_ongoingDownloadSaveDirectory}collection.json",
        _ongoingDownload,
        _ongoingDownloadDownloadedItems,
        True
    )
    filemanager.saveCollectionAsJson(
        f"{_ongoingDownloadSaveDirectory}/collection_backup.json",
        _ongoingDownload,
        _ongoingDownload.localItems,
        True
    )

    onDownloadStopped()

    logger.LogSuccess(
        f"Downloaded collection: {collection.name}\n"
        f"Downloaded items: {len(_ongoingDownloadDownloadedItems)}/{len(collection.fetchedItems)}"
    )


def getSteamDownloaderUrl(item: WorkshopItem):
    '''Returns steamdownloader.io url for item'''
    AssertParameter(item, WorkshopItem, "item")
    if (not SteamAPI.Validator.ValidSteamItemId(item.id)):
        raise ValueError(f"item's ({item}) id is not valid")

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
    raise TimeoutError(
        f"Could not get item ({item}) steamdownloader.io url: timeout reached"
    )


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


def downloadItem(item: WorkshopItem) -> bytes:
    '''Downloads an item'''
    chunkSize = 1024

    if (not SteamAPI.Validator.ValidSteamItemId(item.id) or
                not SteamAPI.Validator.ValidSteamItemId(item.appid)
            ):
        raise Exception(
            "Can't download item without knowing its id or its app id."
        )

    zipFileUrl = getSteamDownloaderUrl(item)

    with io.BytesIO() as memoryFile:
        downloadResponse = requests.get(zipFileUrl, stream=True)
        filesize = downloadResponse.headers.get('content-length')
        if filesize is None:
            logger.LogWarning(
                f"{logger.Indent(2)}Can't track download progress. Downloading {filesize} bytes..."
            )
            memoryFile.write(downloadResponse.content)
        else:
            print(
                f"{logger.Indent(2)}Downloading {logger.ProgressBar(30, 0)}", end="\r"
            )
            for chunk in downloadResponse.iter_content(chunkSize):
                memoryFile.write(chunk)
                fillPercentage = memoryFile.getbuffer().nbytes / int(filesize) * 100
                print(
                    f"{logger.Indent(2)}Downloading {logger.ProgressBar(30, fillPercentage)}", end="\r"
                )
            logger.LogMessage("")
        memoryFile.seek(0)
        return memoryFile.read()

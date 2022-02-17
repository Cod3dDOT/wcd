import json
import requests
import io
import time

from classes import WorkshopCollection
from classes import WorkshopItem

from utils import filemanager, logger
from api import SteamAPI


_ongoingDownload: WorkshopCollection = None


def IsDownloading() -> bool:
    return _ongoingDownload != None


def OngoingDownload() -> WorkshopCollection:
    return _ongoingDownload


def StopDownload():
    global _ongoingDownload

    if IsDownloading():
        logger.LogWarning(
            f"{logger.StartIndent()}Stopping download..."
        )
        _ongoingDownload = None


def UpdateCollection(collection: WorkshopCollection, directory: str, removeOldItems: bool = True, removeDeletedItems: bool = True) -> None:
    '''Checks all items in collection, and updates/adds/removes them as needed\n
    WARNING: collections maybe very big, so this command may generate a lot of internet traffic and take a while.'''
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
        in filemanager.listDirsInDirectory(collectionDirectory)
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

    global _ongoingDownload
    _ongoingDownload = collection

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
            itemDirectory = f"{collectionDirectory}/{item.name}"
            if (filemanager.doesDirectoryExist(itemDirectory)):
                filemanager.deleteDirectory(itemDirectory)

        for folder in willBeDeletedFolders:
            logger.LogError(
                f"{logger.Indent(2)}"
                f"Deleting folder no longer associated with collection: "
                f"{folder}"
            )
            if (filemanager.doesDirectoryExist(f"{collectionDirectory}/{folder}")):
                filemanager.deleteDirectory(f"{collectionDirectory}/{folder}")

    failedToUpdateIds: list[WorkshopItem] = []
    if len(willBeUpdatedIds) > 0:
        logger.LogMessage(
            f"{logger.Indent(1)}Updating {len(willBeUpdatedIds)} old items"
        )

        for index, itemId in enumerate(willBeUpdatedIds):
            newItemIndex = fetchedItemIdsList.index(itemId)
            newItem = collection.fetchedItems[newItemIndex]
            newItemDirectory = f"{collectionDirectory}/{newItem.name}"

            localItemIndex = localItemIdsList.index(itemId)
            localItem = collection.localItems[localItemIndex]
            localItemDirectory = f"{collectionDirectory}/{localItem.name}"

            logger.LogMessage(
                f"{logger.Indent(1)}"
                f"{index}. "
                f"{newItem.name}"
            )

            if (filemanager.doesDirectoryExist(localItemDirectory) and removeOldItems):
                logger.LogMessage(f"{logger.Indent(2)}Deleting old folder...")
                filemanager.deleteDirectory(localItemDirectory)

            if (filemanager.doesDirectoryExist(newItemDirectory)):
                logger.LogMessage(f"{logger.Indent(2)}Deleting old folder...")
                filemanager.deleteDirectory(newItemDirectory)

            try:
                downloadedData = downloadItem(newItem)
                logger.LogMessage(f"{logger.Indent(2)}Extracting...")
                filemanager.saveZipFile(newItemDirectory, downloadedData)
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
            newItemIndex = fetchedItemIdsList.index(itemId)
            newItem = collection.fetchedItems[newItemIndex]
            newItemDirectory = f"{collectionDirectory}/{newItem.name}"

            logger.LogMessage(
                f"{logger.Indent(1)}"
                f"{index}. "
                f"{newItem.name}"
            )

            try:
                downloadedData = downloadItem(newItem)
                logger.LogMessage(f"{logger.Indent(2)}Extracting...")
                filemanager.saveZipFile(newItemDirectory, downloadedData)
            except Exception as exception:
                logger.LogError(
                    f"{logger.Indent(1)}{logger.StartIndent()}Exception occured while trying to download item: \n"
                    f"{logger.Indent(2)}{exception}"
                )
                failedToAddIds.append(newItem.id)

    # this ensures we do not
    #   1. add new items which failed to download
    #   2. update old items which failed to download
    finalItemsList: list[WorkshopItem] = []
    for item in collection.fetchedItems:
        failedToAdd = item.id in failedToAddIds
        failedToUpdate = item.id in failedToUpdateIds

        if (failedToUpdate):
            # If item failed to update, we get the old info for it
            # So basically we leave it untouched
            localItemIndex = localItemIdsList.index(item.id)
            localItem = collection.localItems[localItemIndex]
            finalItemsList.append(localItem)
            continue

        if (failedToAdd):
            # If we failed to add new item, well... we failed
            # Do not write it into json, so that it will download next time
            continue

        # If we managed to get to this point, its either:
        #   1. item was updated successfully
        #   2. item was added successfully
        #   3. item was ignored, as it was up to date
        # Which means, we can safely add them to the final .json file
        finalItemsList.append(item)

    filemanager.saveCollectionAsJson(
        collection, finalItemsList, collectionDirectory
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

    collectionDirectory = f"{directory}/{collection.name}"

    if filemanager.doesDirectoryExist(collectionDirectory):
        if (overrideExistingDirectory):
            filemanager.deleteDirectory(collectionDirectory)
        else:
            logger.LogError(f"Directory already exists: {collectionDirectory}")
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

    # TODO: Do the same as in UpdateCollection()
    filemanager.saveCollectionAsJson(
        collection, collection.fetchedItems, collectionDirectory
    )

    global _ongoingDownload
    _ongoingDownload = collection

    logger.LogMessage(
        f"{logger.Indent(1)}Downloading {len(collection.fetchedItems)} items"
    )

    successfulDownloads = 0
    for index, item in enumerate(collection.fetchedItems):
        logger.LogMessage(
            f"{logger.Indent(1)}"
            f"{index}. "
            f"{item.name}"
        )
        try:
            downloadedData = downloadItem(item)
            itemDirectory = f"{collectionDirectory}/{item.name}"
            if (filemanager.doesDirectoryExist(itemDirectory)):
                filemanager.deleteDirectory(itemDirectory)
            print(f"{logger.Indent(2)}Extracting...")
            filemanager.saveZipFile(itemDirectory, downloadedData)
            successfulDownloads += 1
        except Exception as exception:
            logger.LogError(
                f"{logger.Indent(1)}{logger.StartIndent()}Exception occured while trying to download item: \n"
                f"{logger.Indent(2)}{exception}"
            )

    logger.LogSuccess(
        f"Downloaded collection: {collection.name}. \
        Downloaded items: {successfulDownloads}/{len(collection.fetchedItems)}"
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

import os
import json

from classes.workshopItemBase import WorkshopItemBase
from classes.workshopItem import WorkshopItem

from utils import logger, filemanager
from api import SteamAPI


class WorkshopCollection(WorkshopItemBase):
    localItems: list[WorkshopItem] = []
    newItems: list[WorkshopItem] = []

    def __init__(self, id: str, appid: int = -1, name: str = "", localItems: list[WorkshopItem] = []) -> None:
        if (SteamAPI.Validator.ValidSteamItemId(id)):
            super().__init__(id, appid, name)
            title, appid, newItems = SteamAPI.GetWorkshopCollectionInfo(
                self.id
            )
            self.name = title
            self.appid = appid
            self.newItems = newItems
        else:
            if (len(localItems) > 0):
                super().__init__(id, appid, name)
                self.localItems = localItems
                self.newItems = SteamAPI.GetLocalCollectionInfo(
                    self.localItems
                )
            else:
                raise Exception(
                    "Could not create a collection.\n"
                    f"Params: {id}, {appid}, {name}, {localItems}"
                )

    @classmethod
    def fromUrl(cls, url: str):
        id = SteamAPI.Converter.IdFromUrl(url)
        return cls(id)

    @classmethod
    def fromJson(cls, jsonDict: str):
        id = None
        appid = jsonDict.get("appId")
        name = jsonDict.get("collectionName")
        jsonItems = jsonDict.get("items")

        if (appid is None):
            logger.LogError(
                "Please specify appid for your collection!"
            )
            return

        if (jsonItems is None):
            logger.LogError(
                "You are specifying local collection, but no items were found!"
            )
            return

        if (name is None):
            name = "NotInCollection"

        localItems: list[WorkshopItem] = []
        ids: list[str] = []
        names: list[str] = []
        for jsonItem in jsonItems:
            wItem = WorkshopItem(
                jsonItem.get("itemId"),
                jsonItem.get("appId"),
                jsonItem.get("itemName"),
                jsonItem.get("lastUpdated")
            )
            if (wItem.id is None):
                logger.LogError(
                    f"Error parsing item: {jsonItem}. Item id is not specified!"
                )
                continue

            if (wItem.appid and wItem.appid != appid):
                logger.LogError(
                    f"Error parsing item: {jsonItem}. Item appid does not match collection id!"
                )
                continue

            if (wItem.id in ids or wItem.name in names):
                dups = [
                    x for x
                    in jsonItems
                    if x.id == wItem.id or x.name == wItem.name
                ]
                logger.LogWarning(
                    "Possible duplicates:\n"
                    f"{wItem}"
                )
                for idx, dup in enumerate(dups):
                    logger.LogWarning(f"    {idx}. - {dup}")

            ids.append(wItem.id)
            names.append(wItem.name)
            localItems.append(wItem)

        if (len(localItems) == 0):
            logger.LogError(
                "You are specifying local collection, but no items were parsed successfully!"
            )
            return

        return cls(id, appid, name, localItems)

    def json(self):
        '''Retuns dict with name, id, and app id.'''
        return {"collectionName": self.name, "collectionId": self.id, "appId": self.appid}

    def saveAsJson(self, directory):
        if (not filemanager.doesFolderExist(directory)):
            filemanager.createFolder(directory)

        with open(f"{directory}/collection.json", "w") as file:
            data = self.json()
            data["items"] = [
                item.json() for item
                in self.newItems
            ]
            file.write(json.dumps(data))

    def __str__(self) -> str:
        return f"{{WorkshopCollection - name: {self.name} | id: {self.id} | appid: {self.appid} }}"

    def __repr__(self) -> str:
        return self.__str__()

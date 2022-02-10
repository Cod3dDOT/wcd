import os
import json

from classes.workshopItemBase import WorkshopItemBase
from classes.workshopItem import WorkshopItem

from utils import logger
from api import SteamAPI


class WorkshopCollection(WorkshopItemBase):
    items: list[WorkshopItem] = []

    def __init__(self, id: str, appid: int = -1, name: str = "", items: list[WorkshopItem] = []) -> None:
        self.items = items
        if (SteamAPI.Validator.ValidSteamItemId(id)):
            super().__init__(id, appid, name)
            title, appid, updatedItems = SteamAPI.GetWorkshopCollectionInfo(
                self.id
            )
            self.name = title
            self.appid = appid
            # BAD
            BADFIXItems = []
            for item in updatedItems:
                item.needsUpdate = True
                BADFIXItems.append(item)
            self.updateItemRegisters(BADFIXItems)
        else:
            if (id == "DummyIdForLocalCollection" and len(self.items) > 0):
                super().__init__(id, appid, name)
                itemIds = [x.id for x in self.items]
                updatedItems = SteamAPI.GetItemsUpdatedInfo(itemIds)
                self.updateItemRegisters(updatedItems)
            else:
                raise Exception(
                    f"Workshop collection: incorrect id: {id}"
                )

    def updateItemRegisters(self, updatedItems: WorkshopItem):
        for index, updatedItem in enumerate(updatedItems):
            if (len(self.items) > index):
                if (self.items[index].lastUpdated != updatedItem.lastUpdated):
                    updatedItem.needsUpdate = True
                self.items[index] = updatedItem
            else:
                self.items.append(updatedItem)

    @classmethod
    def fromUrl(cls, url: str):
        id = SteamAPI.Converter.IdFromUrl(url)
        return cls(id)

    @classmethod
    def fromJson(cls, jsonDict: str):
        id = "DummyIdForLocalCollection"  # jsonDict.get("collectionId")
        appid = jsonDict.get("appId")
        name = jsonDict.get("collectionName")
        items = jsonDict.get("items")

        if (appid is None):
            logger.LogError(
                "Please specify appid for your collection!"
            )
            return

        if (items is None):
            logger.LogError(
                "You are specifying local collection, but no items were found!"
            )
            return

        if (name is None):
            name = "NotInCollection"

        wItems: list[WorkshopItem] = []
        ids: list[str] = []
        names: list[str] = []
        for item in items:
            wItem = WorkshopItem(
                int(item.get("itemId")),
                item.get("appId"),
                item.get("itemName"),
                item.get("lastUpdated")
            )
            if (wItem.id is None):
                logger.LogError(
                    f"Error parsing item: {item}. Item id is not specified!"
                )
                continue

            if (wItem.appid and wItem.appid != appid):
                logger.LogError(
                    f"Error parsing item: {item}. Item appid does not match collection id!"
                )
                continue

            if (wItem.id in ids or wItem.name in names):
                dups = [x for x in items
                        if (x.id == wItem.id or x.name == wItem.name)
                        ]
                logger.LogWarning(f"Possible duplicates:\n{wItem}")
                for idx, dup in enumerate(dups):
                    logger.LogWarning(f"    {idx}. - {dup}")
            wItems.append(wItem)

        if (len(wItems) == 0):
            logger.LogError(
                "You are specifying local collection, but no mods were parsed successfully!"
            )
            return

        return cls(id, appid, name, wItems)

    def json(self):
        '''Retuns dict with name, id, and app id.'''
        return {"collectionName": self.name, "collectionId": self.id, "appId": self.appid}

    def saveAsJson(self, directory):
        if (not os.path.exists(directory)):
            os.makedirs(directory)

        with open(f"{directory}/collection.json", "w") as file:
            data = self.json()

            jsonItems = []
            for item in self.items:
                jsonItems.append(item.json())

            data["items"] = jsonItems
            file.write(json.dumps(data))

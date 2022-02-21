
from typing import Optional
from classes import WorkshopItemBase
from classes import WorkshopItem

from utils import logger
from api import SteamAPI


class WorkshopCollectionException(Exception):
    pass


class WorkshopCollection(WorkshopItemBase):
    localItems: list[WorkshopItem] = []
    fetchedItems: list[WorkshopItem] = []

    def __init__(self, id: int, appid: int = -1, name: str = "", localItems: list[WorkshopItem] = []) -> None:
        if (SteamAPI.Validator.ValidSteamItemId(id)):
            super().__init__(id, appid, name)
        elif (len(localItems) > 0):
            super().__init__(id, appid, name)
            self.localItems = localItems
        else:
            raise WorkshopCollectionException(
                "Can't create collection: \n"
                f"id: {id}, appid: {appid}, name: {name}, len(localItems): {len(localItems)}"
            )

    @classmethod
    def fromUrl(cls, url: str):
        id = SteamAPI.Converter.IdFromUrl(url)
        return cls(id)

    @classmethod
    def fromJson(cls, jsonDict: dict):
        id = -1
        appid = jsonDict.get("appId")
        name = jsonDict.get("collectionName")
        jsonItems = jsonDict.get("items")

        if (appid is None):
            logger.LogError(
                "You are specifying local collection, but no appid was found!"
            )
            return None

        if (jsonItems is None):
            logger.LogError(
                "You are specifying local collection, but no items were found!"
            )
            return None

        if (name is None):
            name = "NotInCollection"

        parsedItems: list[WorkshopItem] = []
        parsedItemsIds: list[int] = []
        parsedItemsNames: list[str] = []
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

            if (wItem.id in parsedItemsIds or wItem.name in parsedItemsNames):
                dups = [
                    item for item
                    in jsonItems
                    if item.get("id") == wItem.id or item.get("name") == wItem.name
                ]
                logger.LogWarning(
                    f"Possible duplicates for {wItem}:\n"
                )
                for idx, dup in enumerate(dups):
                    logger.LogWarning(f"{logger.StartIndent()}{idx}. - {dup}")

            parsedItemsIds.append(wItem.id)
            parsedItemsNames.append(wItem.name)
            parsedItems.append(wItem)

        if (len(parsedItems) == 0):
            logger.LogError(
                "You are specifying local collection, but no items were parsed successfully!"
            )
            return None

        return cls(id, appid, name, parsedItems)

    def FetchNewItems(self) -> None:
        if (SteamAPI.Validator.ValidSteamItemId(self.id)):
            try:
                title, appid, fetchedItems = SteamAPI.GetWorkshopCollectionInfo(
                    self.id
                )
                self.name = title
                self.appid = appid
                self.fetchedItems = fetchedItems
            except SteamAPI.SteamAPIException:
                raise WorkshopCollectionException("Collection does not exist.")
        elif (len(self.localItems) > 0):
            self.fetchedItems = SteamAPI.GetLocalCollectionInfo(
                self.localItems
            )

    @staticmethod
    def getItemsByName(items: list[WorkshopItem], name: str) -> list[WorkshopItem]:
        result = [item for item in items if item.name == name]
        return result

    @staticmethod
    def getItemById(items: list[WorkshopItem], id: int) -> Optional[WorkshopItem]:
        if (not SteamAPI.Validator.ValidSteamItemId(id)):
            raise Exception("Item id is not valid")

        result = [item for item in items if item.id == id]
        return result[0] if len(result) > 0 else None

    @staticmethod
    def getItemNames(items: list[WorkshopItem]):
        return [item.name for item in items]

    @staticmethod
    def getItemIds(items: list[WorkshopItem]):
        return [item.id for item in items]

    def json(self):
        '''Retuns dict with name, id, and app id.'''
        return {"collectionName": self.name, "collectionId": self.id, "appId": self.appid}

    def __str__(self) -> str:
        return f"{{WorkshopCollection - name: {self.name} | id: {self.id} | appid: {self.appid} }}"

    def __repr__(self) -> str:
        return self.__str__()

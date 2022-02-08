import io
import zipfile

from classes import WorkshopItemBase
from utils import logger


class WorkshopItem(WorkshopItemBase):
    downloadedData: bytes = None
    needsUpdate: bool = False

    def __init__(self, id: int, appid: int = -1, name: str = "", lastUpdated: str = "", needsUpdate: bool = False) -> None:
        super().__init__(id, appid, name, lastUpdated)
        self.needsUpdate = needsUpdate

    @classmethod
    def fromJson(cls, json):
        return cls(json.get("itemId"), json.get("appId"), json.get("itemName"), json.get("lastUpdated"))

    def json(self):
        '''Returns dict with id, appid, and lastUpdated vars.'''
        return {"itemName": self.name, "itemId": self.id, "appId": self.appid, "lastUpdated": self.lastUpdated}

    def canSaveToDisk(self):
        return self.downloadedData is not None

    def saveToDisk(self, directory) -> bool:
        '''Save mod to directory if it was downloaded before.'''

        if (self.downloadedData == None):
            logger.LogError(
                "Nothing to save to disk. Please download the mod first."
            )
            return False

        print(f"{logger.Indent(2)}Extracting")

        try:
            zipFile = zipfile.ZipFile(io.BytesIO(self.downloadedData))
            zipFile.extractall(f"{directory}/{self.name}")
            return True
        except:
            logger.LogError(
                "Something went wrong while extracting a zip file."
            )
            return False

    def __str__(self) -> str:
        return super().__str__()

    def __repr__(self):
        return super().__repr__()

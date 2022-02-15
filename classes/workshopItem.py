from classes import WorkshopItemBase


class WorkshopItem(WorkshopItemBase):
    def __init__(self, id: int, appid: int = -1, name: str = "", lastUpdated: str = "") -> None:
        super().__init__(id, appid, name, lastUpdated)

    @classmethod
    def fromJson(cls, json):
        return cls(json.get("itemId"), json.get("appId"), json.get("itemName"), json.get("lastUpdated"))

    def json(self):
        '''Returns dict with id, appid, and lastUpdated vars.'''
        return {"itemName": self.name, "itemId": self.id, "appId": self.appid, "lastUpdated": self.lastUpdated}

    def __str__(self) -> str:
        return super().__str__()

    def __repr__(self):
        return super().__repr__()

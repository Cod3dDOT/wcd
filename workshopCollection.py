import requests
from bs4 import BeautifulSoup
import os

from workshopItem import WorkshopItem
from workshopMod import WorkshopMod


class WorkshopCollection(WorkshopItem):
    mods: list[WorkshopMod] = []

    def __init__(self, id, appid="", name="") -> None:
        super().__init__(id, appid, name)

    def getCollectionInfo(self) -> None:
        '''Gets collection name and app id.\n
        Gets name and id for all mods in the collection.'''

        if (self.id == ""):
            print("Can't get collection info without knowing its id.")
            return

        url = self.getSteamUrl()
        html_doc = requests.get(url).text
        soup = BeautifulSoup(html_doc, 'html.parser')

        itemDivs = soup.find_all('div', {'class': "collectionItemDetails"})

        collectionId = url.split("?id=")[1]
        if (collectionId != self.id):
            print(
                "Something went terribly wrong and we got the wrong collection. Exiting."
            )
            return

        self.SetName(
            soup.find(
                'div', {'class': "workshopItemDetailsHeader"}
            ).find(
                'div', {"class": "workshopItemTitle"}
            ).text
        )

        self.SetAppId(
            soup.find(
                'div', {'class': "breadcrumbs"}
            ).find(
                'a', href=True
            )["href"].split("app/")[1]
        )

        for modDiv in itemDivs:
            link = modDiv.find(href=True)
            modName = link.find('div').text
            modId = link['href'].split("?id=")[1]
            modAppid = self.appid
            mod = WorkshopMod(modId, modAppid, modName)
            self.mods.append(mod)

    def download(self, directory, redownload=False):
        '''Downloads all mods in collection.\n
        WARNING: collections maybe very big, so this command may generate a lot of internet traffic and take a while.'''

        if (self.id == "" or self.appid == ""):
            print("Can't download collection without knowing its id or its app id. Call getCollectionInfo() first!")
            return

        print(f"Downloading collection: {self.name}")
        collectionDir = f"{directory}/{self.name}"

        for mod in self.mods:
            print(f"    - {mod.name}")
            modDir = f"{collectionDir}/{mod.name}"
            if (os.path.exists(modDir) and not redownload):
                print(f"            Skipping, mod already downloaded.")
                continue
            mod.download()
            mod.saveToDisk(collectionDir)

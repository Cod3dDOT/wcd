import requests
import os
import json
from bs4 import BeautifulSoup
from termcolor import colored

from workshopItem import WorkshopItem
from workshopMod import WorkshopMod

os.system("")


class WorkshopCollection(WorkshopItem):
    mods: list[WorkshopMod] = []

    def __init__(self, id, appid="", name="", mods: list[WorkshopMod] = []) -> None:
        self.mods = mods
        if (self.id != "" and self.id != None):
            super().__init__(id, appid, name)
            self.getCollectionInfo()
        else:
            if (len(self.mods) > 0):
                super().__init__(id, appid, name)
                print(
                    "Could not get collection name, appID and mods."
                )
            else:
                print(f"Incorrect id: {id}")

    @classmethod
    def fromUrl(cls, url):
        id = WorkshopCollection.getIdFromSteamUrl(url)
        return cls(id)

    @classmethod
    def fromJson(cls, jsonDict):
        id = "" if "collectionId" not in jsonDict else jsonDict["collectionId"]
        appid = "" if "appId" not in jsonDict else jsonDict["appId"]
        name = "" if "collectionName" not in jsonDict else jsonDict["collectionName"]

        if (name == ""):
            name = "NoCollectionFolder"

        mods: list[WorkshopMod] = []
        if "mods" in jsonDict:
            for mod in jsonDict["mods"]:
                wMod = WorkshopMod(
                    mod["modId"], mod["appId"], mod["modName"]
                )
                if (wMod.id == None or wMod.appid == None):
                    print(colored(f"Error parsing mod: {wMod}", "red"))
                else:
                    mods.append(wMod)
        if (len(mods) == 0):
            print(
                colored(
                    "Your collection has no id, and no mods were parsed successfully. Exiting...", "red"
                )
            )
            exit()
        return cls(id, appid, name, mods)

    def json(self):
        '''Retuns dict with name, id, and app id.'''
        return {"collectionName": self.name, "collectionId": self.id, "appId": self.appid}

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

        if ((self.id == "" or self.appid == "") and not (len(self.mods) > 0)):
            print(colored(
                "Can't download collection without knowing its id or its app id. Call getCollectionInfo() first!", "red"))
            return

        print(f"Downloading collection: {self.name}")
        collectionDir = f"{directory}/{self.name}"

        self.saveAsJson(collectionDir)

        successfulDownloads = 0
        for mod in self.mods:
            print(f"    - {mod.name}")
            modDir = f"{collectionDir}/{mod.name}"
            if (os.path.exists(modDir) and not redownload):
                print(
                    colored(f"            Skipping, mod already downloaded.", "yellow"))
                successfulDownloads += 1
                continue
            result = mod.download()
            if (result):
                mod.saveToDisk(collectionDir)
                successfulDownloads += 1

        print(colored(
            f"Downloaded collection: {self.name}. Mods: {successfulDownloads}/{len(self.mods)}", "green"))

    def saveAsJson(self, directory):
        if (not os.path.exists(directory)):
            os.makedirs(directory)
        with open(f"{directory}/collection.json", "w") as file:
            data = self.json()

            modsJson = []
            for mod in self.mods:
                modsJson.append(mod.json())

            data["mods"] = modsJson
            file.write(json.dumps(data))

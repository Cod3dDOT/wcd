from workshopItem import WorkshopItem
from termcolor import colored
import io
import requests
import zipfile
import os
import shutil
import json
import time

os.system("")


def moveFilesUp(root_path, cur_path):
    for filename in os.listdir(cur_path):
        if os.path.isfile(os.path.join(cur_path, filename)):
            shutil.move(os.path.join(cur_path, filename),
                        os.path.join(root_path, filename)
                        )
        elif os.path.isdir(os.path.join(cur_path, filename)):
            moveFilesUp(root_path, os.path.join(cur_path, filename))
    if cur_path != root_path:
        os.rmdir(cur_path)


class WorkshopMod(WorkshopItem):
    cachedData = None

    def __init__(self, modId, appid="", modName="") -> None:
        super().__init__(modId, appid, modName)

    @classmethod
    def fromJson(cls, json):
        return cls(json["modId"], json["appId"], json["modName"])

    def json(self):
        '''Retuns dict with name, id, and app id.'''
        return {"modName": self.name, "modId": self.id, "appId": self.appid}

    def getAdditionalInfo(self) -> None:
        '''Gets mod name and app id.'''

        raise NotImplementedError("Currently nor implemented!")

    def getSteamDownloaderUrl(self):
        requestUrl = "https://node03.steamworkshopdownloader.io/prod/api/download/request"
        requestData = {"publishedFileId": self.id, "collectionId": None,
                       "hidden": False, "downloadFormat": "raw", "autodownload": False}
        requestHeaders = {"Content-type": "application/json"}
        requestResponse = requests.post(
            requestUrl, json=requestData, headers=requestHeaders
        )
        uuid = json.loads(requestResponse.text)["uuid"]

        for _ in range(3):
            statusUrl = "https://node03.steamworkshopdownloader.io/prod/api/download/status"
            statusData = f'''{{"uuids":["{uuid}"]}}'''
            statusHeaders = {"Content-type": "application/json"}
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
            time.sleep(2)

    def GetSteamDownloaderCachedUrl(self):
        url = "http://steamworkshop.download/online/steamonline.php"
        data = {"item": self.id, "app": self.appid}
        headers = {"Content-type": "application/x-www-form-urlencoded"}

        response = requests.post(
            url, data=data, headers=headers
        )

        if (response.text == "" or response.text == "<pre>Sorry, this file is not available. Need re-download.</pre>"):
            print(colored(
                f"            Error downloading. Please try ot download this mod manually.", "red"))
            return False

        zipFileUrl = response.text.split("<a href='")[1].split("'>")[0]
        return zipFileUrl

    def download(self):
        '''Downloads mod and caches it.'''

        if (self.id == "" or self.appid == ""):
            print("Can't download mod without knowing its id or its app id.")
            return

        if (self.cachedData != None):
            return self.cachedData

        zipFileUrl = self.getSteamDownloaderUrl()

        with io.BytesIO() as memfile:
            print(zipFileUrl)
            downloadResponse = requests.get(zipFileUrl, stream=True)
            totalLength = downloadResponse.headers.get('content-length')
            dl = 0
            if totalLength is None:
                memfile.write(downloadResponse.content)
                print(
                    colored("            Can't track download progress. Downloading...", "yellow"))
            else:
                for chunk in downloadResponse.iter_content(1024):
                    dl += len(chunk)
                    memfile.write(chunk)
                    done = int(30 * dl / int(totalLength))
                    print(
                        f"            Downloading [{'=' * done}{' ' * (30-done)}]", end="\r"
                    )
            print("")
            memfile.seek(0)
            self.cachedData = memfile.read()
            return True

    def saveToDisk(self, directory):
        '''Save mod to directory if it was downloaded before.'''
        if (self.cachedData == None):
            print(
                colored("Nothing to save to disk. Please download the mod first.", "red"))
            return

        print(f"            Extracting")

        z = zipfile.ZipFile(io.BytesIO(self.cachedData))
        z.extractall(f"{directory}/{self.name}")
        # moveFilesUp(f"{directory}/{self.name}",
        # f"{directory}/{self.name}/{self.id}"
        # )

    def __str__(self) -> str:
        return super().__str__()

    def __repr__(self):
        return super().__repr__()

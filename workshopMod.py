import io
import requests
import zipfile
import os
import shutil

from workshopItem import WorkshopItem


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

    def __init__(self, id, appid="", name="") -> None:
        super().__init__(id, appid, name)

    def getAdditionalInfo(self) -> None:
        '''Gets mod name and app id.'''

        raise NotImplementedError("Currently nor implemented!")

    def download(self):
        '''Downloads mod ans caches it.'''

        if (self.id == "" or self.appid == ""):
            print("Can't download mod without knowing its id or its app id.")
            return

        if (self.cachedData != None):
            return self.cachedData

        url = "http://steamworkshop.download/online/steamonline.php"
        data = {"item": self.id, "app": self.appid}
        headers = {"Content-type": "application/x-www-form-urlencoded"}

        response = requests.post(
            url, data=data, headers=headers
        )

        if (response.text == ""):
            print(f"            Error downloading. Skipping.")
            return

        zipFileUrl = response.text.split("<a href='")[1].split("'>")[0]

        with io.BytesIO() as memfile:
            downloadResponse = requests.get(zipFileUrl, stream=True)
            totalLength = downloadResponse.headers.get('content-length')
            dl = 0
            if totalLength is None:
                memfile.write(downloadResponse.content)
                print("            Can't track download progress. Downloading...")
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
            return self.cachedData

    def saveToDisk(self, directory):
        '''Save mod to directory if it was downloaded before.'''
        if (self.cachedData == None):
            print("Nothing to save to disk. Please download the mod first.")
            return

        print(f"            Extracting")

        z = zipfile.ZipFile(io.BytesIO(self.cachedData))
        z.extractall(f"{directory}/{self.name}")
        moveFilesUp(f"{directory}/{self.name}",
                    f"{directory}/{self.name}/{self.id}"
                    )

import os
import shutil
import io
import zipfile
import json

from classes import WorkshopCollection
from classes import WorkshopItem
from utils import AssertParameter


def doesDirectoryExist(path: str) -> bool:
    return os.path.isdir(path)


def doesFileExist(path: str) -> bool:
    return os.path.isfile(path)


# def deleteAllDirectoryContents(path: str) -> None:
#     if (not doesDirectoryExist(path)):
#         raise Exception(f"Folder does not exist: {path}")

#     for root, dirs, files in os.walk(path):
#         for f in files:
#             os.unlink(os.path.join(root, f))
#         for d in dirs:
#             shutil.rmtree(os.path.join(root, d))


def deleteDirectory(directory: str) -> None:
    AssertParameter(directory, str, "directory")

    if (not doesDirectoryExist(directory)):
        raise Exception(f"{directory} does not exist!")

    shutil.rmtree(directory)


def createDirectory(directory: str) -> None:
    AssertParameter(directory, str, "directory")
    os.makedirs(directory)


def listDirsInDirectory(directory: str) -> list[str]:
    '''Lists folders in directory'''
    AssertParameter(directory, str, "directory")

    if (not doesDirectoryExist(directory)):
        raise Exception(f"{directory} does not exist!")

    return [
        dir for dir
        in os.listdir(directory)
        if doesDirectoryExist(os.path.join(directory, dir))
    ]


def listFilesInDirectory(directory: str) -> list[str]:
    '''Lists files in directory'''
    AssertParameter(directory, str, "directory")
    return [
        file for file
        in os.listdir(directory)
        if doesFileExist(os.path.join(directory, file))
    ]


def saveZipFile(directory: str, zipFileBytes: bytes):
    '''Extracts bytes of a zipfile to a folder'''
    AssertParameter(directory, str, "directory")
    AssertParameter(zipFileBytes, bytes, "zipFileBytes")

    if (doesDirectoryExist(directory)):
        raise Exception(f"Directory already exists: {directory}")

    zipFile = zipfile.ZipFile(io.BytesIO(zipFileBytes))
    zipFile.extractall(directory)


def saveCollectionAsJson(path: str, collection: WorkshopCollection, items: list[WorkshopItem], overrideFile: False):
    '''Saves collection to .json file. path MUST include filename and end with .json'''
    AssertParameter(path, str, "path")
    AssertParameter(collection, WorkshopCollection, "collection")
    AssertParameter(items, list, "items")
    for item in items:
        AssertParameter(item, WorkshopItem, f"items.{item.name}")

    if (path.split(".")[-1] != "json"):
        raise ValueError(f"path ({path}) must end with .json")

    if (doesFileExist(path) and not overrideFile):
        raise FileExistsError(f"{path} already exists!")

    with open(f"{path}", "w") as file:
        data = collection.json()
        data["items"] = [
            item.json() for item
            in items
        ]
        file.write(json.dumps(data))

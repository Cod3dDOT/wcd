import os
import shutil
import io
import zipfile

from utils import logger


def doesDirectoryExist(path: str) -> bool:
    return os.path.isdir(path)


def doesFileExist(path: str) -> bool:
    return os.path.isfile(path)


def deleteAllDirectoryContents(path: str) -> None:
    if (not doesDirectoryExist(path)):
        raise Exception(f"Folder does not exist: {path}")

    for root, dirs, files in os.walk('/path/to/folder'):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def deleteDirectory(path: str) -> None:
    shutil.rmtree(path)


def createDirectory(path: str) -> None:
    os.makedirs(path)


def listDirsInDirectory(path: str) -> list[str]:
    return (dir for dir
            in os.listdir(path)
            if doesDirectoryExist(os.path.join(path, dir))
            )


def listFilesInDirectory(path: str) -> list[str]:
    return (file for file
            in os.listdir(path)
            if doesFileExist(os.path.join(path, file))
            )


def saveZipFile(directory: str, zipFileBytes: bytes):
    if (zipFileBytes == None):
        raise Exception(
            "zipFileBytes is None."
        )

    if (doesDirectoryExist(directory)):
        raise Exception(
            f"Folder already exists: {directory}"
        )

    zipFile = zipfile.ZipFile(io.BytesIO(zipFileBytes))
    zipFile.extractall(directory)

import os
import shutil
import io
import zipfile

from utils import logger


def doesFolderExist(path: str) -> bool:
    return os.path.isdir(path)


def doesFileExist(path: str) -> bool:
    return os.path.isfile(path)


def deleteFolderContents(path: str) -> None:
    if (not doesFolderExist(path)):
        raise Exception(f"Folder does not exist: {path}")

    for root, dirs, files in os.walk('/path/to/folder'):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def deleteFolder(path: str) -> None:
    shutil.rmtree(path)


def saveZipFile(directory: str, zipFileBytes: bytes):
    if (zipFileBytes == None):
        raise Exception(
            "zipFileBytes is None."
        )

    if (doesFolderExist(directory)):
        raise Exception(
            f"Folder already exists: {directory}"
        )

    zipFile = zipfile.ZipFile(io.BytesIO(zipFileBytes))
    zipFile.extractall(directory)

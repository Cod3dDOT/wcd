import os
import shutil


def doesFolderExist(path):
    os.path.isdir(path)


def doesFileExist(path):
    os.path.isfile(path)


def deleteFolderContents(path):
    if (not doesFolderExist(path)):
        return

    for root, dirs, files in os.walk('/path/to/folder'):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def deletFolder(path):
    shutil.rmtree(path)

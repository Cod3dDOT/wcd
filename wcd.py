from workshopCollection import WorkshopCollection
import argparse
import os


def parseArgs():
    parser = argparse.ArgumentParser()

    parser.add_argument("-cu", "--collectionUrl", type=str, required=True)
    parser.add_argument("-dir", "--directory", type=str,
                        required=False, default="downloads/")
    parser.add_argument("-f", "--force",
                        required=False, action='store_true')

    args = parser.parse_args()
    return args


def main():
    args = parseArgs()
    dir = os.path.abspath(args.directory)
    url = args.collectionUrl
    force = args.force

    wCollectionId = WorkshopCollection.getIdFromSteamUrl(url)
    wCollection = WorkshopCollection(wCollectionId)
    wCollection.getCollectionInfo()
    wCollection.download(dir, force)


if __name__ == "__main__":
    main()

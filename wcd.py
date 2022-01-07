from workshopCollection import WorkshopCollection
import argparse
import os


def parseArgs():
    parser = argparse.ArgumentParser()

    parser.add_argument("-cu",
                        "--collectionUrl",
                        type=str,
                        required=True,
                        help="Steam collection url. Pattern: https://steamcommunity.com/workshop/filedetails/?id=*")

    parser.add_argument("-dir",
                        "--directory",
                        type=str,
                        required=False,
                        default="downloads/",
                        help="Output directory. A folder with collection name will be saved here.")

    parser.add_argument("-f", "--force",
                        required=False,
                        action="store_true",
                        help="Do not skip downloaded mods and redownload them.")

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

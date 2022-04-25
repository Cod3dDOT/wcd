import requests
import json
import re

from classes import WorkshopItem
from utils import logger


class SteamAPIException(Exception):
    pass


class Validator:
    @staticmethod
    def ValidSteamItemUrl(url: str) -> bool:
        '''Checks if steam item url is valid'''
        if (not isinstance(url, str)):
            return False

        regexStrings = [
            "(?:https?:\/\/)?steamcommunity\.com\/sharedfiles\/filedetails\/(?:\?id=)[0-9]+",
            "(?:https?:\/\/)?steamcommunity\.com\/workshop\/filedetails\/(?:\?id=)[0-9]+"
        ]

        matched = True if len(
            [
                string for string
                in regexStrings
                if re.match(string, url)
            ]
        ) > 0 else False

        return matched

    @ staticmethod
    def ValidSteamItemId(id: int) -> bool:
        '''Checks if steam item id is valid'''
        return isinstance(id, int) and id > 0


class Converter:
    @ staticmethod
    def IdFromUrl(url: str) -> int:
        '''Returns id from steam url.'''
        if (not Validator.ValidSteamItemUrl(url)):
            return -1
        id = int(url.split("?id=")[1])
        if (not Validator.ValidSteamItemId(id)):
            return -1
        return id

    @ staticmethod
    def UrlFromId(id: int) -> str:
        '''Returns steam url from id.'''
        if (not Validator.ValidSteamItemId(id)):
            raise SteamAPIException("Id is not valid")
        return f"https://steamcommunity.com/sharedfiles/filedetails/?id={id}"


class ISteamRemoteStorage:
    @ staticmethod
    def GetCollectionDetails(collectionId: int) -> dict:
        '''Returns id from steam url.'''
        if (not Validator.ValidSteamItemId(collectionId)):
            raise SteamAPIException(
                f"Collection id is not valid: {collectionId}"
            )

        apiString = "http://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1"

        data = {"collectioncount": 1, "publishedfileids[0]": collectionId}
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        response = requests.post(
            apiString, data=data, headers=headers
        )
        try:
            reponseDictionary = json.loads(response.text)
        except:
            raise SteamAPIException(
                f"{logger.StartIndent()}Uknown error occurred while trying to fetch collection details.\n"
                f"{logger.Indent(1)}Error occured while decoding json response from steam API.\n"
                f"{logger.Indent(1)}Response status code: {response.status_code}."
            )
        if (not "response" in reponseDictionary):
            raise SteamAPIException(
                f"{logger.StartIndent()}Uknown error occurred while trying to fetch collection details.\n"
                f"{logger.Indent(1)}Steam API returned empty response.\n"
                f"{logger.Indent(1)}Response status code: {response.status_code}."
            )

        steamApiResult = reponseDictionary["response"]["result"]
        if (steamApiResult != 1):
            raise SteamAPIException(
                f"{logger.StartIndent()}Uknown error occurred while trying to fetch collection details.\n"
                f"{logger.Indent(1)}Steam API returned result code: {steamApiResult}"
            )

        collectitonDetails = reponseDictionary["response"]["collectiondetails"][0]
        collectionSteamApiResult = collectitonDetails["result"]
        if (collectionSteamApiResult != 1):
            if (collectionSteamApiResult == 9):
                raise SteamAPIException("Collection does not exist!")
            else:
                raise SteamAPIException(
                    f"{logger.StartIndent()}Uknown error occurred while trying to fetch collection details.\n"
                    f"{logger.Indent(1)}Steam api returned result code: {collectionSteamApiResult}"
                )
        return collectitonDetails

    @ staticmethod
    def GetPublishedFileDetails(fileIdList: list[int]) -> dict:
        apiUrl = "http://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1"

        data = {}
        validItems = 0
        for fileId in fileIdList:
            if (not Validator.ValidSteamItemId(fileId)):
                logger.LogWarning(
                    f"{logger.StartIndent()}Invalid file id: {fileId}, type: {type(fileId)}"
                )
            else:
                data[f"publishedfileids[{validItems}]"] = fileId
                validItems += 1
        data["itemcount"] = validItems

        headers = {"Content-type": "application/x-www-form-urlencoded"}
        response = requests.post(
            apiUrl, data=data, headers=headers
        )
        try:
            reponseDictionary = json.loads(response.text)
        except:
            raise SteamAPIException(
                f"{logger.StartIndent()}Uknown error occurred while trying to fetch published file details.\n"
                f"{logger.Indent(1)}Error occured while decoding json response from steam api.\n"
                f"{logger.Indent(1)}Response status code: {response.status_code}."
            )

        if (not "response" in reponseDictionary):
            raise SteamAPIException(
                f"{logger.StartIndent()}Uknown error occurred while trying to fetch published file details.\n"
                f"{logger.Indent(1)}Steam api returned empty response.\n"
                f"{logger.Indent(1)}Response status code: {response.status_code}."
            )

        steamApiResult = reponseDictionary["response"]["result"]
        if (steamApiResult != 1):
            raise SteamAPIException(
                f"{logger.StartIndent()}Uknown error occurred while trying to fetch published file details.\n"
                f"\n{logger.Indent(1)}Steam api returned result code: {steamApiResult}"
            )

        publishedFileDetails = reponseDictionary["response"]["publishedfiledetails"]
        return publishedFileDetails


def GetWorkshopCollectionInfo(collectionId: int) -> tuple[str, int, list[WorkshopItem]]:
    '''Returns collection name, appid and list of workshop items'''

    collectionDetails = None
    try:
        collectionDetails = ISteamRemoteStorage.GetCollectionDetails(
            collectionId
        )
    except SteamAPIException as exception:
        raise SteamAPIException(
            f"Exception occurred while trying to get collection information:\n"
            f"{exception}"
        )

    collectionItemsIdList = [
        int(item["publishedfileid"]) for item
        in collectionDetails["children"]
        if (item["filetype"] == 0)
    ]

    UpdatedItemsInfo = GetItemsInfo(
        [collectionId] + collectionItemsIdList
    )
    collectionName = UpdatedItemsInfo[0].name
    collectionAppId = UpdatedItemsInfo[0].appid

    return (
        collectionName,
        collectionAppId,
        UpdatedItemsInfo[1:]
    )


def GetLocalCollectionInfo(collectionItems: list[WorkshopItem]) -> list[WorkshopItem]:
    return GetItemsInfo([item.id for item in collectionItems])


def GetItemsInfo(fileIdList: list[int]) -> list[WorkshopItem]:
    try:
        items = ISteamRemoteStorage.GetPublishedFileDetails(
            fileIdList
        )
    except SteamAPIException as exception:
        raise SteamAPIException(
            f"Exception occurred while trying to get updated items info:\n"
            f"{exception}"
        )

    for item in items:
        status = item["result"]
        if (status != 1):
            if (status == 9):
                logger.LogWarning(
                    f"{logger.StartIndent()}{item['publishedfileid']}: Workshop item does not exist."
                )
            else:
                logger.LogWarning(
                    f"{logger.StartIndent()}{item['publishedfileid']}: Could not fetch workshop item."
                )

    return [
        WorkshopItem(
            int(item["publishedfileid"]),
            int(item["consumer_app_id"]),
            item["title"],
            int(item["time_updated"])
        ) for item
        in items
        if item["result"] == 1
    ]

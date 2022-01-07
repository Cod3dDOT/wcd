import unicodedata
import re


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode(
            'ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


class WorkshopItem:
    name: str = ""
    id: str = ""
    appid: str = ""

    def __init__(self, id, appid="", name="") -> None:
        self.id = id
        self.appid = appid
        self.name = slugify(name)

    def getSteamUrl(self):
        '''Returns mod steam url.'''
        return f"https://steamcommunity.com/workshop/filedetails/?id={self.id}"

    def json(self):
        '''Retuns dict with name, id, and app id.'''
        return {"name": self.name, "id": self.id, "appid": self.appid}

    @staticmethod
    def getIdFromSteamUrl(url):
        '''Returns mod id from steam url.'''
        return url.split("?id=")[1]

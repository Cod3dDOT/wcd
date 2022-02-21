import unicodedata
import re

from utils import AssertParameter


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


class WorkshopItemBase:
    _name: str = ""
    _id: int = -1
    _appid: int = -1
    _lastupdated: int = -1

    def __init__(self, id: int, appid: int = -1, name: str = "", lastUpdated: int = -1) -> None:
        self.id = id
        self.appid = appid
        self.name = name
        self.lastUpdated = lastUpdated

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        AssertParameter(value, int, "id.value")
        self._id = value

    @property
    def appid(self) -> int:
        return self._appid

    @appid.setter
    def appid(self, value: int) -> None:
        AssertParameter(value, int, "appid.value")
        self._appid = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        AssertParameter(value, str, "name.value")
        self._name = slugify(value)

    @property
    def lastUpdated(self) -> int:
        return self._lastupdated

    @lastUpdated.setter
    def lastUpdated(self, value: int) -> None:
        AssertParameter(value, int, "lastUpdated.value")
        self._lastupdated = value

    def __str__(self) -> str:
        return f"{{WorkshopItemBase - name: {self.name} | id: {self.id} | appid: {self.appid} | lastUpdated: {self.lastUpdated}}}"

    def __repr__(self) -> str:
        return self.__str__()

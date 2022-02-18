from termcolor import colored
import os

from utils import AssertParameter

os.system("")


def ProgressBar(length: int, percentage: float) -> str:
    '''Creates a progress bar where max amount of filled bars = length.'''
    AssertParameter(length, int, "length")
    AssertParameter(percentage, (int, float), "percentage")

    if (length < 1):
        raise ValueError("Length of progress bar must be greater than 0!")

    if (percentage < 0 or percentage > 100):
        raise ValueError("Fill percentage must be in range [0, 100]")

    filledBars = int(
        length *
        percentage / 100
    )
    return f"[{'=' * filledBars}{' ' * (length - filledBars)}]"


def YesOrNoQuery(question: str, default: bool = True, yesTooltip: str = "", noTooltip: str = "") -> bool:
    '''Creates a yes/no prompt with question, tooltips and default value. Returns True/False for yes/no'''
    AssertParameter(question, str, "question")
    AssertParameter(default, bool, "default")
    AssertParameter(yesTooltip, str, "yesTooltip")
    AssertParameter(noTooltip, str, "noTooltip")

    valid = {"yes": True, "y": True, "no": False, "n": False}

    yesTooltipText = f": {yesTooltip} " if yesTooltip != "" else " "
    noTooltipText = f": {noTooltip}" if noTooltip != "" else ""

    if (default is None):
        prompt = f"\n[y{yesTooltipText}/ n{noTooltipText}]"
    elif (default):
        prompt = f"\n[Y{yesTooltipText}/ n{noTooltipText}]"
    elif (not default):
        prompt = f"\n[y{yesTooltipText}/ N{noTooltipText}]"
    else:
        raise ValueError(f"Invalid default answer: '{default}'")

    while True:
        LogWarning(question + prompt)
        choice = input().lower()
        if (default is not None and choice == ""):
            return default
        elif (choice in valid):
            return valid[choice]
        else:
            yesValid = "/".join([item for item in valid if valid[item]])
            noValid = "/".join([item for item in valid if not valid[item]])
            LogError(
                f"Please respond with {yesValid} for yes, {noValid} for no.\n"
            )


def StartIndent() -> str:
    '''Retuns start indent'''
    return " - "


def Indent(level: int) -> str:
    '''Retuns indent multiplied by level'''
    AssertParameter(level, int, "level")
    return "   " * level


def LogSuccess(message: str) -> None:
    '''Prints green-colored success message'''
    print(colored(message, "green"))


def LogMessage(message: str) -> None:
    '''Prints message'''
    print(message)


def LogWarning(warning: str) -> None:
    '''Prints yellow-colored warning message'''
    print(colored(warning, "yellow"))


def LogError(error: str) -> None:
    '''Prints red-colored error message'''
    print(colored(error, "red"))

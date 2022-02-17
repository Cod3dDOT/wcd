from termcolor import colored
import os

os.system("")


def ProgressBar(length: int, percentage: int):
    filledBars = int(
        length *
        percentage / 100
    )
    return f"[{'=' * filledBars}{' ' * (length - filledBars)}]"


def StartIndent():
    return " - "


def Indent(indentLevel):
    return "   " * indentLevel


def LogSuccess(message: str):
    print(colored(message, "green"))


def LogMessage(message: str):
    print(message)


def LogWarning(warning: str):
    print(colored(warning, "yellow"))


def LogError(error: str):
    print(colored(error, "red"))

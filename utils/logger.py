from typing import Iterable
from termcolor import colored
import os
import sys
import itertools
import time
import threading

from utils import AssertParameter

os.system("")


class Spinner:
    spinner: Iterable = []
    delay: float = 0
    busy: bool = False
    spinner_visible: bool = False

    def __init__(self, message: str, delay: float = 0.1):
        self.spinner = itertools.cycle(['-', '/', '|', '\\'])
        self.delay = delay
        self.busy = False
        self.spinner_visible = False
        sys.stdout.write(message)

    def write_next(self):
        with self._screen_lock:
            if not self.spinner_visible:
                sys.stdout.write(next(self.spinner))
                self.spinner_visible = True
                sys.stdout.flush()

    def remove_spinner(self, cleanup=False):
        with self._screen_lock:
            if self.spinner_visible:
                sys.stdout.write('\b')
                self.spinner_visible = False
                if cleanup:
                    sys.stdout.write(' ')       # overwrite spinner with blank
                    sys.stdout.write('\r')      # move to next line
                sys.stdout.flush()

    def spinner_task(self):
        while self.busy:
            self.write_next()
            time.sleep(self.delay)
            self.remove_spinner()

    def __enter__(self):
        if sys.stdout.isatty():
            self._screen_lock = threading.Lock()
            self.busy = True
            self.thread = threading.Thread(target=self.spinner_task)
            self.thread.start()

    def __exit__(self, exception, value, tb):
        if sys.stdout.isatty():
            self.busy = False
            self.remove_spinner(cleanup=True)
        else:
            sys.stdout.write('\r')


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


def Up() -> str:
    return '\x1B[1F'


def Clear() -> str:
    return '\x1B[0K'


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


def LogMessage(message: str, end: str = "\n") -> None:
    '''Prints message'''
    print(message, end=end)


def LogWarning(warning: str, end: str = "\n") -> None:
    '''Prints yellow-colored warning message'''
    print(colored(warning, "yellow"), end=end)


def LogError(error: str, end: str = "\n") -> None:
    '''Prints red-colored error message'''
    print(colored(error, "red"), end=end)

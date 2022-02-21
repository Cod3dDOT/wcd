from typing import Type


def AssertParameter(param, paramTypes: Type, paramName):
    if (not isinstance(param, paramTypes)):
        raise TypeError(
            f"{paramName} must be of type {paramTypes}\n"
            f"{paramName}: {param}, type: {type(param)}"
        )

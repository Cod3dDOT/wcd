def AssertParameter(param, paramTypes: tuple, paramName):
    if (not isinstance(param, paramTypes)):
        raise TypeError(
            f"{paramName} must be of type {paramTypes}\n"
            f"{paramName}: {param}, type: {type(param)}"
        )

from micropython import const


# NVM register numbers
class Register:
    BOOTCNT = const(0)
    ERRORCNT = const(7)
    FLAG1 = const(16)


class Flag1:
    SOFTBOOT: int = 0
    BROWNOUT: int = 3
    SHUTDOWN: int = 5
    BURNED: int = 6
    USE_FSK: int = 7


flag_register_lookup: dict[int, type] = {16: Flag1}


def register_lookup(cls: type, index: int) -> str:
    d = {key: getattr(cls, key) for key in dir(cls) if not key.startswith("__")}
    lookup = {value: key for key, value in d.items()}
    return lookup.get(index, "Unknown")

from micropython import const


# NVM register numbers
class Register:
    BOOTCNT = const(0)
    ERRORCNT = const(7)
    FLAG = const(16)


register = {
    key: getattr(Register, key) for key in dir(Register) if not key.startswith("__")
}
lookup = {value: key for key, value in register.items()}

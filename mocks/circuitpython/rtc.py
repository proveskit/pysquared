class RTC:
    _instance = None
    datetime = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RTC, cls).__new__(cls)
            cls._instance.datetime = None
        return cls._instance

    @classmethod
    def destroy(cls):
        cls._instance = None

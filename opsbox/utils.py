class SingletonMeta(type):
    """This metaclass is used to create a Singleton class. The Singleton class
    ensures that only one instance of the class is created and that all
    subsequent instances return the same instance.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

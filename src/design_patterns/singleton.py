from typing import Any

from pydantic._internal._model_construction import ModelMetaclass
from src.core.log import get_logger

logger = get_logger(__name__)


class Singleton(ModelMetaclass):
    """Metaclass that ensures only one instance of each class exists.

    Implements the singleton pattern by maintaining a registry of instances
    and returning the existing instance when a class is instantiated multiple times.
    """

    _instances = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Control instance creation to enforce singleton pattern.

        Args:
            *args: Positional arguments for class constructor.
            **kwargs: Keyword arguments for class constructor.

        Returns:
            The singleton instance of the class.
        """
        if cls not in cls._instances:
            logger.info(f"creating instance of {cls.__name__}")
            instance = cls.__new__(cls, *args, **kwargs)
            instance.__init__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

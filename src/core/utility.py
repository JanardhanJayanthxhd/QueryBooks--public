import re
import time
from dataclasses import dataclass
from hashlib import sha256

from passlib.context import CryptContext
from src.core.log import get_logger

logger = get_logger(__name__)


def clean_llm_output(text: str) -> str:
    """Removes Markdown bold markers and cleans up all extraneous whitespace
    and special characters."""
    cleaned_text = re.sub(r"\*\*", "", text)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    cleaned_text = cleaned_text.replace("*", "").replace("_", "").replace("\\", "")

    return cleaned_text


@dataclass
class CacheDetails:
    """
    Basic cache details used in src.core.cache's functions
    """

    user_id: int
    question: str


def get_elapsed_time_till_now_in_ms(start_time: float) -> float:
    """
    Calculates the duration between a given start time and the current moment in milliseconds.

    This utility is commonly used for performance profiling, such as measuring
    the latency of an LLM API call or a database query.

    Args:
        start_time (float): The starting timestamp as a float, typically
            obtained from a previous call to `time.perf_counter()`.

    Returns:
        float: The elapsed time in milliseconds (ms).
    """
    return (time.perf_counter() - start_time) * 1000


pwt_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password using Argon2.
    Each call generates a unique hash due to random salt.

    Args:
        password: plain text password

    Returns:
        str: hashed password with embedded salt
    """
    return pwt_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if plain text password matches the stored hash.
    The hash contains the salt, so verification extracts it automatically.

    Args:
        plain_password: plain text password from user
        hashed_password: hashed password from database

    Returns:
        bool: True if passwords match, False otherwise
    """
    return pwt_context.verify(plain_password, hashed_password)


def hash_bytes(data: bytes) -> str:
    """Computes the SHA-256 hash of a bytes object.

    Checks if the input is of type bytes, generates a SHA-256 hash, and
    returns the hexadecimal representation. If the input type is invalid,
    triggers an error logging sequence.

    Args:
        data: The bytes data to be hashed.

    Returns:
        str: The hexadecimal string representation of the hash.

    Raises:
        Note: If 'data' is not bytes, it calls unknown_type_while_hashing,
        which logs an error but does not explicitly raise a Python exception.
    """
    if isinstance(data, bytes):
        hash = sha256(data)
        return hash.hexdigest()
    unknown_type_while_hashing(_type=type(data))


def hash_str(data: str) -> str:
    """Computes the SHA-256 hash of a string.

    Encodes the input string into UTF-8 before generating a SHA-256 hash
    and returning the hexadecimal representation. If the input type is
    invalid, triggers an error logging sequence.

    Args:
        data: The string to be hashed.

    Returns:
        str: The hexadecimal string representation of the hash.

    Raises:
        Note: If 'data' is not a string, it calls unknown_type_while_hashing,
        which logs an error.
    """
    if isinstance(data, str):
        hash = sha256(data.encode("utf-8"))
        return hash.hexdigest()
    unknown_type_while_hashing(_type=type(data))


def unknown_type_while_hashing(_type: type) -> None:
    """Logs an error message when an unsupported data type is provided for hashing.

    This utility is called by hashing functions to provide consistent error
    reporting when type validation fails.

    Args:
        _type: The Python type class that was found to be incompatible.

    Returns:
        None
    """
    logger.error(f"Cannot encrypt {_type}")
    return

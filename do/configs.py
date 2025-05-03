"""
Secret management utilities for the Do application.

This module provides functions for loading secrets from a TOML file or environment variables,
with support for dataclass-based configuration models.
"""

import dataclasses
import os
from functools import cache
from pathlib import Path
from typing import Any, Type
import tomllib


FLOWSTATE_DIR = Path(".do")
if Path().resolve().name == "tests":
     FLOWSTATE_DIR = Path("..") / ".do"

SECRETS_FILE = (FLOWSTATE_DIR / "secrets.toml").resolve()


def get_secrets[T](key: str, model: Type[T]) -> T:
    """
    Get secrets for a specific key and convert them to a dataclass instance.

    This function first tries to load secrets from the secrets.toml file.
    If the key is not found, it falls back to environment variables.

    Args:
        key: The section key in the secrets file
        model: The dataclass type to instantiate with the secrets

    Returns:
        An instance of the specified dataclass populated with the secrets
    """
    secrets = load_secrets(SECRETS_FILE)
    if key not in secrets:
        return get_secrets_from_env(key, model)

    return model(**secrets[key])


def get_secrets_from_env[T](key: str, model: Type[T]) -> T:
    """
    Get secrets from environment variables and convert them to a dataclass instance.

    This function looks for environment variables in the format KEY_FIELD,
    where KEY is the uppercase version of the key parameter and FIELD is the
    uppercase version of each field in the dataclass.

    Args:
        key: The prefix for environment variables
        model: The dataclass type to instantiate with the secrets

    Returns:
        An instance of the specified dataclass populated with values from environment variables
    """
    values = {
        name: os.environ.get(f"{key.upper()}_{name.upper()}", field.default)
        for name, field in model.__dataclass_fields__.items()
        if f"{key.upper()}_{name.upper()}" in os.environ or not isinstance(field.default, dataclasses._MISSING_TYPE)
    }
    return model(**values)


def get_secret[T](key: str, *, default: Any = None) -> T:
    """
    Get a single secret value.

    This function first tries to load the secret from the secrets.toml file.
    If the key is not found, it falls back to environment variables.

    Args:
        key: The key of the secret
        default: The default value to return if the secret is not found

    Returns:
        The secret value, or the default value if not found
    """
    secrets = load_secrets(SECRETS_FILE)
    if key in secrets.get("Secrets", {}):
        return secrets[key]

    return os.environ.get(key, default)


@cache
def load_secrets(path: Path) -> dict[str, Any]:
    """
    Load secrets from a TOML file.

    This function is cached, so subsequent calls with the same path will
    return the same result without re-reading the file.

    Args:
        path: The path to the secrets TOML file

    Returns:
        A dictionary containing the secrets from the TOML file
    """
    with path.resolve().open("rb") as f:
        return tomllib.load(f)

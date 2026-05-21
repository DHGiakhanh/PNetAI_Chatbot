"""Domain layer package for PetBot.

This package contains pure business rules: entities, value objects,
enums and domain-specific exceptions. It must not depend on
infrastructure or external services.
"""

from .entities import *
from .value_objects import *
from .enums import *
from .exceptions import *

__all__ = ["entities", "value_objects", "enums", "exceptions"]
# src/petbot/domain package

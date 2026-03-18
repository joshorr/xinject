"""
Things not meant to be part of the public interface go under the `xinject._private` module.

Import useful private utilities/classes/objects directly in here, so you can access them via
`_private.xyz`; Thereby, you can import `from xinject import _private` and use them without
exposing them directly as part of a modules public interface.
"""

from .classproperty import classproperty
from .atomic_counter import AtomicCounter

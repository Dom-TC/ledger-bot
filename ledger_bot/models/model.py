"""The base data model for AirTable records."""

import logging

log = logging.getLogger(__name__)


class Model:
    def __init__(self, **kwargs):
        for attr in self.attributes:
            setattr(self, attr, kwargs.get(attr))

    def __str__(self):
        attrs = ", ".join(f"{attr}={getattr(self, attr)!r}" for attr in self.attributes)
        return f"{self.__class__.__name__}({attrs})"

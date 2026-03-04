"""Architecture generators."""

from archai.architects.base import Architect, ArchitectureType
from archai.architects.monolithic import MonolithicArchitect
from archai.architects.microservices import MicroservicesArchitect
from archai.architects.serverless import ServerlessArchitect
from archai.architects.event_driven import EventDrivenArchitect
from archai.architects.hexagonal import HexagonalArchitect

__all__ = [
    "Architect",
    "ArchitectureType",
    "MonolithicArchitect",
    "MicroservicesArchitect",
    "ServerlessArchitect",
    "EventDrivenArchitect",
    "HexagonalArchitect",
]

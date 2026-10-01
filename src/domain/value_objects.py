"""
value_objects.py – Value objects and enumerations for HTB RAG domain.
"""

from enum import Enum


class QueryScope(str, Enum):
    BROAD = "broad"
    SPECIFIC = "specific"


class AttackPhase(str, Enum):
    RECON = "recon"
    FOOTHOLD = "foothold"
    LATERAL = "lateral_movement"
    PRIVESC = "privesc"


class OS(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    UNKNOWN = "unknown"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    INSANE = "insane"

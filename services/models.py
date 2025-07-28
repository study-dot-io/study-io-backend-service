from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid
import time

class DeckState(Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

@dataclass
class Deck:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    color: str = "#6366F1"
    isSynced: bool = False
    isPublic: bool = True
    state: DeckState = DeckState.ACTIVE
    studySchedule: int = 0
    streak: int = 0

class CardType(Enum):
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3

@dataclass
class Card:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deckId: str = ""
    type: CardType = CardType.NEW
    due: int = field(default_factory=lambda: int(time.time() * 1000))
    front: str = ""
    back: str = ""
    tags: str = ""
    isSynced: bool = False
    createdAt: int = field(default_factory=lambda: int(time.time() * 1000))

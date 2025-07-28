from dataclasses import dataclass
from typing import List, TypedDict
import sys

class Deck(TypedDict, total=False):
    id: str

class Card(TypedDict, total=False):
    id: str
    deckId: str

@dataclass
class SyncData:
    decks: List[Deck]
    cards: List[Card]

class SyncService:
    def __init__(self, db):
        self.db = db

    def sync_data(self, user_id: str, sync_data: SyncData):
        batch = self.db.batch()

        for deck in sync_data.decks:
            deck_id = deck.get("id")
            if not deck_id:
                raise ValueError("Deck must have an id")
            batch.set(self.db.collection("users").document(user_id).collection("decks").document(deck_id), deck)
        for card in sync_data.cards:
            deck_id = card.get("deckId")
            card_id = card.get("id")
            if not card_id:
                raise ValueError("Card must have an id")
            if not deck_id:
                raise ValueError("Card must have a deckId")
            batch.set(self.db.collection("users").document(user_id).collection("decks").document(deck_id).collection("cards").document(card_id), card)

        batch.commit()


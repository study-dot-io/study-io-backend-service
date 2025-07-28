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
    def _get_all_sync_data(self, user_id: str) -> SyncData:
        """
        Fetch all decks and all cards for the given user and return as SyncData.
        """
        decks_ref = self.db.collection("users").document(user_id).collection("decks")
        decks_snap = decks_ref.stream()
        decks = []
        cards = []
        for deck_doc in decks_snap:
            deck = deck_doc.to_dict()
            deck["id"] = deck_doc.id
            decks.append(deck)
            # Fetch cards for this deck
            cards_ref = decks_ref.document(deck_doc.id).collection("cards")
            cards_snap = cards_ref.stream()
            for card_doc in cards_snap:
                card = card_doc.to_dict()
                card["id"] = card_doc.id
                card["deckId"] = deck_doc.id
                cards.append(card)
        return SyncData(decks=decks, cards=cards)

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

        get_all_sync_data = self._get_all_sync_data(user_id)

        return get_all_sync_data

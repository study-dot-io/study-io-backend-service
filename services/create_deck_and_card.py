
import hashlib
import uuid
import time
from enum import Enum

class CreateDeckAndCard:
    '''
    Class responsible for creating the decks and cards we get from the LLM
    '''
    def __init__(self, db, uid: str):
        self.db = db
        self.uid = uid
    def create_deck(self, deck_name: str) -> dict:
        '''
        uid: comes from the validated user token
        deck_name: name for the deck gen by LLM
        '''
        deck_id = str(uuid.uuid4())
        deck = {
            "id": deck_id,
            "name": deck_name,
            "createdAt": int(time.time())
        }
        self.db.collection("users").document(self.uid)\
        .collection("decks").document(deck_id).set(deck)
        return deck
        
    def create_card(self, deck_id: str, front: str, back: str) -> dict:
        card_id = str(uuid.uuid4())
        card = {
            "id": card_id,
            "deckId": deck_id,
            "front": front,
            "back": back,
            "createdAt": int(time.time())
        }
        self.db.collection("users").document(self.uid) \
        .collection("decks").document(deck_id) \
        .collection("cards").document(card_id).set(card)
        return card

    def convert_llm_response(self, content: list, file_name: str) -> list:
        '''
        Assuming the llm has the following response
        {
            "front": "front text",
            "back": "back text"
        }
        We want to convert this to the same schema as the app
        Current architecture choice:
        For each document, llm makes a deck
        This deck has a collection of cards
        '''
        # Make one deck for each file
        llm_deck = self.create_deck(file_name)
        completed_cards = []
        # Iter over the cards in the content and make a card 
        for card in content:
            try:
                new_card = self.create_card(llm_deck["id"], card["front"], card["back"])
                completed_cards.append(new_card)
            # Maybe dont want this card creation to be blocking
            except Exception as e:
                print('Error in card creation: ', e)
                continue
        return (completed_cards, llm_deck)
                
            
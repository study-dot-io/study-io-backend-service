
import hashlib
import uuid
import time
from enum import Enum

def compute_file_hash(file_content: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def create_deck(uid: str, deck_name: str, file_hash:str) -> str:
    '''
    uid: comes from the validated user token
    deck_name: name for the deck gen by LLM
    file_hash: hash for the file computed
    '''
    deck_id = str(uuid.uuid4())
    deck = {
        "id": deck_id,
        "name": deck_name,
        "fileHash": file_hash,
        "createdAt": int(time.time())
    }
    db.collection("users").document(user_id)\
      .collection("decks").document(deck_id).set(deck)
    return deck_id

# Dont think it's required here -> user fills this in
class CardType(Enum):
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3
    
def create_card(deck_id: str, front: str, back: str) -> str:
    card_id = str(uuid.uuid4())
    card = {
        "id": card_id,
        "deckId": deck_id,
        "front": front,
        "back": back,
        "createdAt": int(time.time())
    }
    db.collection("users").document(user_id)\
      .collection("cards").document(card_id).set(deck)
    return card_id

def convert_llm_response(uid: str, file_hash: str, content: list, file_name: str) -> dict:
    '''
    Assuming the llm has the following response
    {
        "front1": "back1" -> card content
    }
    We want to convert this to the same schema as the app
    Current architecture choice:
    For each document, llm makes a deck
    This deck has a collection of cards
    Also want to store filehash in the deck - modify on app
    '''
    # Make one deck for each file
    llm_deck_id = create_deck(uid, file_name, file_hash)
    # Iter over the cards in the content and make a card 
    for card in content:
        new_card = create_card(llm_deck_id, card.front, card.back)
        
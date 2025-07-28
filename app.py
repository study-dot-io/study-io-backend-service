from flask import Flask, request, jsonify
from pdf_utils import extract_text_and_chunks
from services.llm import generate_flashcards
from services.firebase_client import Firebase
from firebase_admin import auth
from services.create_deck_and_card import CreateDeckAndCard
from services.sync import SyncService, SyncData
import base64

db = Firebase.init_db()
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return '<p> Home </p>'
    
@app.route('/generate_flashcards', methods=['POST'])
def generate():
    '''
    From the client app we are expecting a json with this structure
    {
        "login_token": TOKEN,
        "file_name": FILE_NAME
        "file": PDF_FILE,
        "deck_id": deck id
    }
    '''
    response = {
        "authenticated": False,
        "file_name": None,
        "cards": None,
        "deck": None
    }
    data = request.get_json()
    try:
        if not data:
            response["error"] = "Missing request"
            return jsonify(response, 400)
        
        token = data.get("login_token")
        user_id = Firebase.verify_token(token)
        
        if not user_id:
            response["error"] = "Unauthorized"
            return jsonify(response, 401)
        
        response["authenticated"] = True
        
    except auth.ExpiredIdTokenError:
        response["error"] = "Expired"
        return jsonify(response, 401)
    except auth.InvalidIdTokenError:
        response["error"] = "Invalid token"
        return jsonify(response, 401)
    except Exception as e:
        response["error"] = f"Error: {e}"
        return jsonify(response, 401)
    
    create_deck_and_card = CreateDeckAndCard(db, user_id)
    
    
    file_b64 = data.get('file')
    if not file_b64:
        response["Error"] = "Missing file"
        return jsonify(response, 401)
    pdf_file_bytes = base64.b64decode(file_b64) 
    file_name = data.get('file_name')
    
    try:
        text_chunks = extract_text_and_chunks(pdf_file_bytes)
        cards = []
        for chunk in text_chunks:
            chunk_cards = generate_flashcards(chunk)
            if chunk_cards:
                cards += chunk_cards
        # Add the cards and the deck to the db
        final_cards, deck = create_deck_and_card.convert_llm_response(cards, file_name)
        # Currently returning a list of card ids -> easy for 
        response["cards"] = final_cards
        response["deck"] = deck
        print(response)
        return jsonify(response, 200)
    except Exception as e:
        response["error"] = f"Error: {e}"
        return jsonify(response, 401)

@app.route('/sync', methods=['POST'])
def sync():
    '''
    Syncs data between the client and the server.
    '''
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request"}), 400

        token = data.get("token")
        if not token:
            return jsonify({"error": "Missing login token"}), 400

        body = SyncData(decks=data.get("decks", []), cards=data.get("cards", []))
        user_id = Firebase.verify_token(token)

        sync_service = SyncService(db)
        sync_service.sync_data(user_id, body)

        return jsonify({}), 200
    
    except Exception as e:
        return jsonify({"error": f"Error: {e}"}), 500
        
    
#Sync service goes here

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
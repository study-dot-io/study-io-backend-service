from flask import Flask, request, jsonify
from pdf_utils import extract_text_and_chunks
from services.llm import generate_flashcards
from services.firebase_client import Firebase
from services.create_deck_and_card import CreateDeckAndCard

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
        "file": PDF_FILE
    }
    '''
    response = {
        "authenticated": False,
        "cards": None,
    }
    try:
        data = request.get_json()
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
    
    create_deck_and_card = CreateDeckAndCard(db, uid)
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    pdf_file = request.files['file']
    try:
        text_chunks = extract_text_and_chunks(pdf_file)
        cards = []
        for chunk in text_chunks:
            chunk_cards = generate_flashcards(chunk)
            if chunk_cards:
                cards += chunk_cards
        # Add the cards and the deck to the db
        final_cards = create_deck_and_card.convert_llm_response(cards, pdf_file.filename)
        # Currently returning a list of card ids -> easy for 
        response["cards"] = final_cards
        return jsonify(response, 200)
    except Exception as e:
        response["error"] = f"Error: {e}"
        return jsonify(response, 401)
        
    
#Sync service goes here

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
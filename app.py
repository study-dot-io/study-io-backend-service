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
    token = request.form.get("login_token")
    # user_id = Firebase.verify_token(token)
    user_id = "aditya_final_test123"
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
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
        print(f'card: {cards[0]}')
        # Add the cards and the deck to the db
        final_cards = create_deck_and_card.convert_llm_response(cards, pdf_file.filename)
        # Currently returning a list of card ids -> easy for 
        return jsonify({"cards": final_cards}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#Sync service goes here

if __name__ == '__main__':
    app.run(debug=True)
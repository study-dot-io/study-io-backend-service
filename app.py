from flask import Flask, request, jsonify
from pdf_utils import extract_text_and_chunks
from services.llm import generate_flashcards
from services.firebase_client import Firebase
from services.create_deck_and_card import convert_llm_response
db = Firebase.init_db()
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    print('home')
    return '<p> Home page </p>'

@app.route('/test-db', methods=['GET'])
def test_db():
    print('h1')
    try:
        collections = list(db.collections())
        if collections:
            print('got')
            return jsonify({"collections": str(len(collections))})
        else:
            print('dont have but okay')
            return jsonify({"message": "Success"})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/test-deck-creation', methods=['GET'])
def test_deck_creation():
    print('hi')
    content = [
        {"test1": "back1"},
        {"test2": "back2"},
        {"test3": "back3"},
    ]
    dummy_uid = "dummyuid"
    dummy_deck_name = "testdeck"
    dummy_file_hash = "filehash"
    convert_llm_response(dummy_uid, dummy_file_hash, content, dummy_file_name)
    return jsonify({"cards": len(cards)})
    
    
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
    user_id = Firebase.verify_token(token)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
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
        return jsonify(cards), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#Sync service goes here

if __name__ == '__main__':
    app.run(debug=True)
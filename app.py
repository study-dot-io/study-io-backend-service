from flask import Flask, request, jsonify
from pdf_utils import extract_text_and_chunks
from services.llm import generate_flashcards
from services.firebase_client import Firebase

db = Firebase.init_db()
app = Flask(__name__)

@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        collections = list(db.collections)
        if collections:
            print('got')
            return jsonify({"collections": str(len(collections))})
        else:
            print('dont have but okay')
            return jsonify({"message": "Success"})
    except Exception as e:
        return jsonify({"Error": e})

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
from flask import Flask, request, jsonify
# from auth import verify_token
from pdf_utils import extract_text_and_chunks
from llm import generate_flashcards

app = Flask(__name__)

@app.route('/generate_flashcards', methods=['POST'])
def generate():
    #auth
    # token = request.headers.get("Authorization", "").replace("Bearer ", "")
    # user_id = verify_token(token)
    # if not user_id:
    #     return jsonify({"error": "Unauthorized"}), 401
    
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
from Flask import Flask, request, jsonify
from auth import verify_token
from pdf_utils import extract_text_and_chunks
from llm import generate_flashcards
from storage import save_flashcards

app = Flask(__name__)

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
    user_id = verify_token(token)
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    pdf_file = request.files['file']
    text_chunks = extract_text_and_chunks(pdf_file)

    cards = []
    for chunk in text_chunks:
        cards += generate_flashcards(chunk)

    return jsonify(cards), 200

# @app.route('/sync_flashcards', methods=['POST'])
# def sync():
#     token = request.headers.get("Authorization", "").replace("Bearer ", "")
#     user_id = verify_token(token)
#     if not user_id:
#         return jsonify({"error": "Unauthorized"}), 401

#     data = request.get_json()
#     flashcards = data.get("flashcards")
#     title = data.get("document_title")
#     course = data.get("course")

#     save_flashcards(user_id, course, title, flashcards)
#     return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(debug=True)
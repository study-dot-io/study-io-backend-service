from flask import Flask, request, jsonify
from pdf_utils import extract_text_and_chunks
from services.llm import generate_flashcards
from services.firebase_client import Firebase
from services.create_deck_and_card import CreateDeckAndCard
from google.cloud import firestore


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
            return jsonify(response), 400
        
        token = data.get("login_token")
        user_id = Firebase.verify_token(token)
        
        if not user_id:
            response["error"] = "Unauthorized"
            return jsonify(response), 401
        
        response["authenticated"] = True
        
    except auth.ExpiredIdTokenError:
        response["error"] = "Expired"
        return jsonify(response), 401
    except auth.InvalidIdTokenError:
        response["error"] = "Invalid token"
        return jsonify(response), 401
    except Exception as e:
        response["error"] = f"Error: {e}"
        return jsonify(response), 401
    
    create_deck_and_card = CreateDeckAndCard(db, user_id)
    
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
        return jsonify(response), 200
    except Exception as e:
        response["error"] = f"Error: {e}"
        return jsonify(response), 401
        
@app.route('/get_all_friends', methods=['GET'])
def get_all_friends():
    '''
    Given your uid, return the all the friends you have
    '''
    response = {
        "friends": None
    }
    try:
        data = request.get_json()
        if not data:
            response["error"] = "Missing request"
            return jsonify(response), 400
        
        token = data.get("login_token")
        user_id = Firebase.verify_token(token)
        
        if not user_id:
            response["error"] = "Unauthorized"
            return jsonify(response), 401
        
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            response["error"] = "User not found"
            return jsonify(response), 404
        
        user_data = user_doc.to_dict()
        friend_ids = user_data.get('friends', [])
        friend_result = []
        for friend_id in friend_ids:
            curr_friend = db.collection('users').document(friend_id).get()
            if curr_friend.exists:
                curr_friend_dict = curr_friend.to_dict()
                curr_friend_dict['id'] = friend_id
                friend_result.append(curr_friend_dict)
        response['friends'] = friend_result
        return jsonify(response), 200
    except Exception as e:
        response['error'] = e
        return jsonify(response), 400
    
                
@app.route('/add_friend', methods=["POST"])
def add_friend():
    """
    Given the email of someone, add them as your friend.
    """
    response = {
        "friend_id": None,
        "uid": None
    }

    data = request.get_json()
    if not data:
        response["error"] = "Missing request"
        return jsonify(response), 400

    token = data.get("login_token")
    email = data.get("email")  

    if not token or not email:
        response["error"] = "Missing token or email"
        return jsonify(response), 400

    # user_id = Firebase.verify_token(token)
    # if not user_id:
    #     response["error"] = "Unauthorized"
    #     return jsonify(response), 401

    users_ref = db.collection('users')

    # Find friend by email
    friend_query = users_ref.where('email', '==', email).limit(1).stream()
    friend_doc = next(friend_query, None)

    if not friend_doc or not friend_doc.exists:
        response["error"] = "Friend not found"
        return jsonify(response), 404

    friend_data = friend_doc.to_dict()
    friend_id = friend_doc.id

    try:
        users_ref.document(user_id).update({
            'friends': firestore.ArrayUnion([friend_id])
        })

        users_ref.document(friend_id).update({
            'friends': firestore.ArrayUnion([user_id])
        })

        response["friend_id"] = friend_id
        response["uid"] = user_id
        return jsonify(response), 200

    except Exception as e:
        print(f"Error adding friend: {e}")
        response["error"] = "Failed to add friend"
        return jsonify(response), 500

#Sync service goes here

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
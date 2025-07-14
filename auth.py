#need help from auth peeps probs, adding rough code tho

import firebase_admin
from firebase_admin import auth, credentials
import os
from flask import jsonify
from dotenv import load_dotenv

load_dotenv()

FIREBASE_PATH = os.getenv("FIREBASE_PATH")
cred = credentials.Certificate(FIREBASE_PATH)
firebase_admin.initialize_app(cred)

def verify_token(token: str) -> str:
    '''
    Given a login token verify the user before allowing them to access the service
    '''
    try:
        decoded = auth.verify_id_token(token)
        return decoded["uid"]
    except Exception as e:
        return e
    

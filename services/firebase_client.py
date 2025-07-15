import firebase_admin
from firebase_admin import auth, credentials, firestore
import os
from flask import jsonify
from dotenv import load_dotenv

load_dotenv()
FIREBASE_PATH = os.getenv("FIREBASE_PATH")

class Firebase:
    _app = None
    _db = None
    
    @classmethod
    def init_db(cls):
        '''
        Initialize the firestore db, should only be called once
        '''
        if not cls._app:        
            cred = credentials.Certificate(FIREBASE_PATH)
            cls._app = firebase_admin.initialize_app(cred)
            cls._db = firestore.client()
        return cls._db
    @staticmethod
    def verify_token(token: str) -> str:
        '''
        Given a login token verify the user before allowing them to access the service
        '''
        try:
            decoded = auth.verify_id_token(token)
            return decoded["uid"]
        except Exception as e:
            return e
    

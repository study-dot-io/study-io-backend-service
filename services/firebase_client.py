from typing import Any

import firebase_admin
from firebase_admin import auth, credentials, firestore
import os
import json
from dotenv import load_dotenv

load_dotenv()
FIREBASE_PATH = os.getenv("FIREBASE_PATH")
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")

class Firebase:
    _app = None
    _db = None
    
    @classmethod
    def init_db(cls):
        '''
        Initialize the firestore db, should only be called once
        '''
        if not cls._app:
            if FIREBASE_CREDENTIALS:
                # Use credentials from environment variable (production)
                cred_dict = json.loads(FIREBASE_CREDENTIALS)
                cred = credentials.Certificate(cred_dict)
            elif FIREBASE_PATH:
                # Use credentials from file path (local development)
                cred = credentials.Certificate(FIREBASE_PATH)
            else:
                raise ValueError("Either FIREBASE_CREDENTIALS or FIREBASE_PATH must be set")
            
            cls._app = firebase_admin.initialize_app(cred)
            cls._db = firestore.client()
        return cls._db

    @staticmethod
    def verify_token(token: str):
        '''
        Given a login token verify the user before allowing them to access the service
        Returns the user ID string if valid, None if invalid
        '''
        try:
            decoded = auth.verify_id_token(token)
            return decoded["uid"]
        except Exception as e:
            # Log the error and return None instead of the exception object
            print(f"Token verification failed: {str(e)}")
            return None

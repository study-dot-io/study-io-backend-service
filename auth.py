#need help from auth peeps probs, adding rough code tho

# import firebase_admin
# from firebase_admin import auth, credentials
# import os

# cred = credentials.Certificate("path/to/firebase-adminsdk.json")
# firebase_admin.initialize_app(cred)

# def verify_token(token):
#     try:
#         decoded = auth.verify_id_token(token)
#         return decoded["uid"]
#     except Exception:
#         return None
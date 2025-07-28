import base64
import logging
import os
from functools import wraps

from firebase_admin import auth
from flask import Flask, request, jsonify

from file_utils import extract_text_and_chunks, DependencyError
from services.firebase_client import Firebase
from services.llm import generate_flashcards
from services.sync import SyncService, SyncData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase
db = Firebase.init_db()
app = Flask(__name__)


class APIResponse:
    """Standardized API response structure"""

    @staticmethod
    def success(data=None, message="Success"):
        response = {"success": True, "message": message}
        if data:
            response["data"] = data
        return response

    @staticmethod
    def error(message, error_type="error", status_code=400):
        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": message
            }
        }, status_code


def require_auth(f):
    """Decorator to handle authentication for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            data = request.get_json()
            if not data:
                return jsonify(*APIResponse.error("Missing request body"))

            token = data.get("login_token") or data.get("token")
            if not token:
                return jsonify(*APIResponse.error("Missing authentication token", "unauthorized", 401))

            user_id = Firebase.verify_token(token)
            if not user_id:
                return jsonify(*APIResponse.error("Invalid authentication token", "unauthorized", 401))

            # Pass user_id and data to the decorated function
            return f(user_id, data, *args, **kwargs)

        except auth.ExpiredIdTokenError:
            return jsonify(*APIResponse.error("Authentication token expired", "expired", 401))
        except auth.InvalidIdTokenError:
            return jsonify(*APIResponse.error("Invalid authentication token", "invalid_token", 401))
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify(*APIResponse.error("Authentication failed", "auth_error", 401))

    return decorated_function


def process_file_chunks(file_bytes):
    """Extract text chunks from file and generate flashcards"""
    try:
        logger.info("Extracting text and chunks from file")
        text_chunks = extract_text_and_chunks(file_bytes)
        logger.info(f"Extracted {len(text_chunks)} chunks")

        cards = []
        for i, chunk in enumerate(text_chunks):
            logger.info(f"Processing chunk {i+1}/{len(text_chunks)}")
            chunk_cards = generate_flashcards(chunk)
            if chunk_cards:
                # Convert Flashcard objects to dictionaries for JSON serialization
                cards.extend([card.to_dict() for card in chunk_cards])

        return cards
    except Exception as e:
        logger.error(f"Error processing file chunks: {str(e)}")
        raise


def validate_file_data(data):
    """Validate file-related data from request"""
    file_b64 = data.get('file')
    if not file_b64:
        raise ValueError("Missing file data")

    file_name = data.get('file_name')
    if not file_name:
        raise ValueError("Missing file name")

    try:
        file_bytes = base64.b64decode(file_b64)
        return file_bytes, file_name
    except Exception as e:
        raise ValueError(f"Invalid file encoding: {str(e)}")


@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify(APIResponse.success({"status": "running", "service": "study-io-backend"}))


@app.route('/generate_flashcards', methods=['POST'])
@require_auth
def generate_flashcards_endpoint(user_id, data):
    """
    Generate flashcards from uploaded file

    Expected JSON structure:
    {
        "login_token": "TOKEN",
        "file_name": "FILE_NAME",
        "file": "BASE64_ENCODED_FILE",
    }
    """
    try:
        # Validate file data
        file_bytes, file_name = validate_file_data(data)

        # Process file and generate cards
        cards = process_file_chunks(file_bytes)

        if not cards:
            return jsonify(*APIResponse.error("No flashcards could be generated from the file"))

        logger.info(f"Generated {len(cards)} flashcards from file '{file_name}' for user {user_id}")

        cards = {"cards": cards}
        print(cards)
        return jsonify(APIResponse.success(cards, "Flashcards generated successfully"))

    except ValueError as e:
        return jsonify(*APIResponse.error(str(e), "validation_error", 400))
    except DependencyError as e:
        logger.error(f"Dependency error: {str(e)}")
        return jsonify(*APIResponse.error(
            f"Missing system dependency: {str(e)}. Please contact support.",
            "dependency_error",
            500
        ))
    except Exception as e:
        logger.error(f"Error generating flashcards: {str(e)}")
        return jsonify(*APIResponse.error("Failed to process file", "processing_error", 500))


@app.route('/sync', methods=['POST'])
@require_auth
def sync_endpoint(user_id, data):
    """
    Sync data between client and server

    Expected JSON structure:
    {
        "token": "TOKEN",
        "decks": [...],
        "cards": [...]
    }
    """
    try:
        # Extract sync data
        sync_data = SyncData(
            decks=data.get("decks", []),
            cards=data.get("cards", [])
        )

        # Perform sync
        sync_service = SyncService(db)
        sync_service.sync_data(user_id, sync_data)

        logger.info(f"Successfully synced data for user {user_id}")
        return jsonify(APIResponse.success(message="Data synced successfully"))

    except Exception as e:
        logger.error(f"Error syncing data for user {user_id}: {str(e)}")
        return jsonify(*APIResponse.error("Failed to sync data", "sync_error", 500))


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify(*APIResponse.error("Endpoint not found", "not_found", 404))


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify(*APIResponse.error("Method not allowed", "method_not_allowed", 405))


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify(*APIResponse.error("Internal server error", "internal_error", 500))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'

    logger.info(f"Starting application on port {port} with debug={debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

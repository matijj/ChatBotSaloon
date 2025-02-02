"""
Module: app.py
Purpose: 
    - Main entry point for the Flask web application.
    - Maps Dialogflow intents (actions) to their respective handler functions.
    - Serves a chatbot UI using an `index.html` template.

Folder Structure:
    - `templates/index.html`: Contains the chatbot user interface.
    - `utils/action_handlers.py`: Contains functions for handling specific Dialogflow actions.
    - `run.py`: Starts the Flask app by calling this module.
"""




from flask import Flask, request, jsonify, render_template, request 

import json

import os
import logging
from utils.action_handlers import (
    default_welcome_intent,
    handle_user_wants_to_schedule_appointment,
    handle_user_provides_name,
    handle_user_provides_email,
    handle_user_confirms_no_changes,
    handle_user_wants_to_update,
    handle_fallback_intent,
    handle_user_chooses_name,
    handle_user_chooses_email,
    handle_user_updates_name,
    handle_user_updates_email,
    handle_user_provides_date_time,
    handle_user_denies_note,
    handle_user_confirms_note,
	handle_user_provides_note,
    handle_user_chooses_date_time,  # Add this
    handle_user_updates_date_time, # Add this
    handle_user_confirms_slot, #NOVO
    handle_user_denies_slot,
     handle_user_chooses_note,  # Add this
     handle_user_updates_note,        # Add this
    handle_user_confirms_slot_update, # Add this
	handle_user_denies_slot_update,
    handle_user_wants_products,
    handle_user_wants_tea_tree_shampoo,
    handle_user_wants_shampoo_one,
    handle_user_wants_double_hitter_shampoo,
)



# Set up logging
logging.basicConfig(level=logging.INFO)



# Initialize the Flask app
app = Flask(
    __name__,
    template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '../templates'))
)




# Mapping Dialogflow actions to their handler functions
# This dictionary links action names (from Dialogflow) to the corresponding handler functions.
action_handlers = {
    'defaultWelcomeIntent': default_welcome_intent,
	'userWantsToScheduleAppointment': handle_user_wants_to_schedule_appointment,
    'userProvidesNameIntent': handle_user_provides_name,
    'userProvidesEmailIntent': handle_user_provides_email,
    'userProvidesDateTime': handle_user_provides_date_time,  # New mapping
    'userDeniesNote': handle_user_denies_note,               # New mapping
    'userChoosesDateTimeUpdate': handle_user_chooses_date_time,  # Map this
    'userUpdatesDateTime': handle_user_updates_date_time,        # Map this
    'userConfirmsSlot': handle_user_confirms_slot,  # Map this
    'userDeniesSlot': handle_user_denies_slot,
	'userConfirmsNote': handle_user_confirms_note,  # New mapping
	'userProvidesNote': handle_user_provides_note,  # New mapping
    'userChoosesNoteUpdate': handle_user_chooses_note,  # Add this
    'userUpdatesNote': handle_user_updates_note,        # Add this
    'userConfirmsSlotUpdate': handle_user_confirms_slot_update,  # Map this
    'userDeniesSlotUpdate': handle_user_denies_slot_update,  # Add this mapping
    'userConfirmsNoChangesIntent': handle_user_confirms_no_changes,
    'userWantsToUpdateIntent': handle_user_wants_to_update,
    'userChoosesNameIntent': handle_user_chooses_name,
    'userChoosesEmailIntent': handle_user_chooses_email,
    'userUpdatesNameIntent': handle_user_updates_name,
    'userUpdatesEmailIntent': handle_user_updates_email,
    'defaultFallbackIntent': handle_fallback_intent,
    'userWantsProducts': handle_user_wants_products,
    'userWantsTeaTreeShampoo': handle_user_wants_tea_tree_shampoo,
    'userWantsShampooOne': handle_user_wants_shampoo_one,
    'userWantsDoubleHitterShampoo': handle_user_wants_double_hitter_shampoo,
}





# Route for serving the chatbot UI
@app.route('/')
def home():
    """
    Renders the chatbot UI.
    The UI is served from `templates/index.html`.
    """

    return render_template('index.html')  




@app.route('/static/<path:filename>', methods=['GET'])
def serve_static_file(filename):
    """Serve static files (images) from the correct directory."""
    try:
        static_dir = os.path.join(os.path.dirname(__file__), "static")  # ✅ Correct path

        if not os.path.exists(os.path.join(static_dir, filename)):
            logging.warning(f"[app.py] Static file not found: {filename}")
            return jsonify({"error": f"Static file '{filename}' not found."}), 404

        logging.info(f"[app.py] Serving static file: {filename}")
        return send_from_directory(static_dir, filename)

    except Exception as e:
        logging.error(f"[app.py] Error serving static file '{filename}': {e}", exc_info=True)
        return jsonify({"error": "An error occurred while serving the static file."}), 500





@app.route('/webhook', methods=['POST'])
def handle_webhook():

    """
    Main webhook endpoint for processing requests from Dialogflow.

    Steps:
        1. Parse and validate the incoming request.
        2. Extract the 'action' field from the request body.
        3. Route the request to the appropriate handler function.
        4. Handle errors from the handler or webhook process.
        5. Log and return the response to Dialogflow.
    
    Returns:
        Flask Response: JSON response for Dialogflow's fulfillment.
    """

    try:
        logging.info("=== Entering app.py -> handle_webhook ===")

        # Step 1: Parse and validate the incoming request
        body = request.get_json()
        if not body:
            logging.warning("[app.py] Missing request body")
            return jsonify({"error": "Missing request body"}), 400

        if 'queryResult' not in body:
            logging.warning("[app.py] Missing 'queryResult' in request body")
            return jsonify({"error": "Missing 'queryResult' in request body"}), 400

        if 'action' not in body['queryResult']:
            logging.warning("[app.py] Missing 'action' in 'queryResult'")
            return jsonify({"error": "Missing 'action' in 'queryResult'"}), 400

        #logging.info(f"[app.py] Incoming request body: {json.dumps(body, indent=2)}")

        # Step 2: Extract the action
        action = body['queryResult']['action']
        logging.info(f"[app.py] Extracted action: {action}")

        # Step 3: Route to the appropriate handler
        handler = action_handlers.get(action)
        if handler:
            try:
                logging.info(f"[app.py] Calling handler: {handler.__name__}")
                response_data = handler(body)
            except Exception as handler_error:
                logging.error(f"[app.py] Error in handler '{handler.__name__}': {handler_error}", exc_info=True)
                response_data = {
                    "fulfillmentMessages": [
                        {"text": {"text": ["Sorry, something went wrong while processing your request."]}}
                    ]
                }
        else:
            logging.warning(f"[app.py] No handler found for action: {action}")
            response_data = {"fulfillmentMessages": [{"text": {"text": ["Sorry, I didn’t understand."]}}]}

        # Step 4: Log and return the response
        logging.info(f"[app.py] Response sent to Dialogflow: {json.dumps(response_data, indent=2)}")
        logging.info("=== Exiting app.py -> handle_webhook ===")
        return jsonify(response_data)

    except Exception as e:
        logging.error("[app.py] Error handling webhook:", exc_info=True)
        return jsonify({"error": "Something went wrong"}), 500



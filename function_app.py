import azure.functions as func
import json
import logging
from email_processor import process_email
 
app = func.FunctionApp()
 
@app.route(route="process-email", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def process_email_request(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Email received for processing")
    try:
        body = req.get_json()
        email_data = {
            "from": body.get("from"),
            "subject": body.get("subject"),
            "body": body.get("body"),
            "received_at": body.get("received_at"),
        }
        result = process_email(email_data)
        return func.HttpResponse(
            json.dumps(result, default=str), status_code=200, mimetype="application/json"
        )
    except Exception as e:
        import traceback
        logging.error(f"Error: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return func.HttpResponse(str(e), status_code=500)

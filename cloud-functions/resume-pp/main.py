import functions_framework
import firebase_admin
from firebase_admin import firestore
import os
import requests

COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "ping-pong-translations")
LANGUAGE_CODES = os.environ.get("LANGUAGE_CODES", ["pol_Latn", "eng_Latn", "deu_Latn", "fra_Latn", "zho_Hans", "jpn_Jpan"])
MAX_TRANSLATION_LENGTH = os.environ.get("MAX_TRANSLATION_LENGTH", 250)
PP_URL = os.environ.get("PP_URL", "https://web-translator-ubxvqaxota-lm.a.run.app")

app = firebase_admin.initialize_app()
db = firestore.client()


class LoopedError(Exception):
    pass

class RunningError(Exception):
    pass

@firestore.transactional
def lock_status(transaction, document_ref):
    # Check if status is paused, if so, change to pending (to continue translating)
    document = document_ref.get(transaction=transaction)
    status = document.get("Status")
    if status == "Paused":
        transaction.update(document_ref, {"Status": "Pending", "PingPongModifyDate": firestore.SERVER_TIMESTAMP})
    elif status == "Looped":
        raise LoopedError
    elif status == "Running":
        raise RunningError

@functions_framework.http
def resume_pp(request):
    id = request.form.get("id", None)
    if id is None:
        return {"status": "fail-empty"}, 500
    lock_transaction = db.transaction()
    document_ref = db.collection(COLLECTION_NAME).document(id)

    try:
        lock_status(lock_transaction, document_ref)
    except LoopedError:
        return {"status": "fail-looped"}, 500
    except RunningError:
        return {"status": "fail-running"}, 500
    # invoke translating model
    url = PP_URL + "/" + str(id)
    res = requests.post(url)
    res_dict = res.json()
    if res_dict["status"] != "success":
        return {"status": "fail-toResume"}, 500
    return {"status": "success"}, 200

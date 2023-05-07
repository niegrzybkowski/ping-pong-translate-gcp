import functions_framework
import firebase_admin
from firebase_admin import firestore
from flask import redirect
import os
import requests
import threading

COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "ping-pong-translations")
LANGUAGE_CODES = os.environ.get("LANGUAGE_CODES", ["pol_Latn", "eng_Latn", "deu_Latn", "fra_Latn", "zho_Hans", "jpn_Jpan"])
MAX_TRANSLATION_LENGTH = os.environ.get("MAX_TRANSLATION_LENGTH", 250)
PP_URL = os.environ.get("PP_URL", "https://web-translator-ubxvqaxota-lm.a.run.app")
SITE_URL = os.environ.get("SITE_URL", "https://ping-pong-translate.web.app/view")

app = firebase_admin.initialize_app()
db = firestore.client()

class InvalidLangError(Exception):
    pass

class TextLengthError(Exception):
    pass

def check_validity(ln_tra, ln_pro, text):
    # Check validity of entry data
    if ln_tra not in LANGUAGE_CODES or ln_pro not in LANGUAGE_CODES:
        raise InvalidLangError
    if len(text) > MAX_TRANSLATION_LENGTH:
        raise TextLengthError

@firestore.transactional
def get_status_id(transaction, document_ref):
    # Get existing ping pong status and ID from Firestore - as found with the query
    document = document_ref.get(transaction=transaction)
    status = document.get("Status")
    id = document.id
    return status, id

def start_translating(url):
    requests.post(url, verify=False)

@functions_framework.http
def initialize_pp(request):
    # get arguments from request
    ln_tra = request.form.get("ln_tra", None)
    ln_pro = request.form.get("ln_pro", None)
    text = request.form.get("OriginalText", None)
    if ln_tra is None or ln_pro is None or text is None:
        return {"status": "empty-fail"}, 500
    # query for existing document with those arguments
    col_ref = db.collection(COLLECTION_NAME)
    exists_query = col_ref.where(
        "OriginalText", "==", text).where(
        "ToLanguage", "==", ln_tra).where(
        "FromLanguage", "==", ln_pro).get()
    if len(exists_query) > 0: # if document found and not pending, return associated view page
        get_transaction = db.transaction()
        status, id = get_status_id(get_transaction, exists_query[0].reference)
        if status != "Pending":
            return redirect(SITE_URL + "/" + str(id))
    else: # add new document
        try:
            check_validity(ln_tra, ln_pro, text)
        except InvalidLangError:
            return {"status": "fail-lang"}, 500
        except TextLengthError:
            return {"status": "fail-textLength"}, 500

        data = {
            "FromLanguage": ln_pro,
            "ToLanguage": ln_tra,
            "OriginalText": text,
            "CreateDate": firestore.SERVER_TIMESTAMP,
            "Status": "Pending",
        }
        _, city_ref = col_ref.add(data)
        id = city_ref.id
    # invoking the translation model
    url = PP_URL + "/" + str(id)
    thread = threading.Thread(target=start_translating, args=(url,))
    thread.start()

    return redirect(SITE_URL + "/" + str(id))
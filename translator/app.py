import os 

COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "ping-pong-translations") 
NUMBER_REPEATS = os.environ.get("NUMBER_REPEATS", 5) 

import firebase_admin
from firebase_admin import firestore

app = firebase_admin.initialize_app()
db = firestore.client()


from translator import PingPong

@firestore.transactional
def lock_status(transaction, document_ref):
    document = document_ref.get(transaction=transaction)
    status = document.get("Status")
    if status == "Pending":
        transaction.update(document_ref, {"Status": "Running", "PingPongModifyDate": firestore.SERVER_TIMESTAMP})
        return True
    else:
        return False

@firestore.transactional
def finalize(transaction, document_ref, ping_pong):
    document = document_ref.get(transaction=transaction)
    status = document.get("Status")
    if status == "Running":
        transaction.update(
            document_ref, 
            {
                "Status": "Looped" if ping_pong.is_looped else "Paused",
                "Translations": ping_pong.translation_list,
                "PingPongModifyDate": firestore.SERVER_TIMESTAMP 
            }
        )
        return True
    else:
        return False

class UnableToLockError(Exception):
    pass

class UnableToFinalizeError(Exception):
    pass

def fill_in_translations(document_id):
    lock_transaction = db.transaction()
    document_ref = db.collection(COLLECTION_NAME).document(document_id)
    
    successful_lock = lock_status(lock_transaction, document_ref)
    if not successful_lock:
        raise UnableToLockError
    
    document = document_ref.get().to_dict()

    pp = PingPong(
        from_language=document["FromLanguage"],
        to_language=document["ToLanguage"], 
        original_text=document["OriginalText"], 
        number_repeats=NUMBER_REPEATS
    )

    if "Translations" in document:
        pp.translation_list = document["Translations"]
    else:
        document_ref.update({"Translations": firestore.ArrayUnion([document["OriginalText"]])})

    for translation in pp.run_generator():
        document_ref.update({"Translations": firestore.ArrayUnion([translation])})

    finalize_transaction = db.transaction()
    successful_finalization = finalize(finalize_transaction, document_ref, pp)
    if not successful_finalization:
        raise UnableToFinalizeError


from flask import Flask

app = Flask(__name__)

@app.route('/<document_id>', methods = ["POST"])
def fill_in_server(document_id):
    try:
        fill_in_translations(document_id)
        print("SUCCESS: Filled in translations.")
        return {"status": "success"}, 200
    except UnableToLockError:
        print("WARNING: Failed to lock document.")
        return {"status": "fail-retry"}, 503
    except UnableToFinalizeError:
        print("ERROR: Failed to finalize document!")
        return {"status": "fail"}, 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

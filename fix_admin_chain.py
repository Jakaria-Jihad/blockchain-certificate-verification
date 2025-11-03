import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def fix_admin_chain(collection_name):
    students = db.collection(collection_name).stream()
    for s in students:
        doc_id = s.id
        doc = s.to_dict()
        updated = False

        # Ensure admin_chain exists and is a list
        if 'admin_chain' not in doc or not isinstance(doc['admin_chain'], list):
            doc['admin_chain'] = [{"admin_id": "N/A", "role": "N/A", "actions": ["No modifications recorded"]}]
            updated = True
        else:
            # Ensure each entry has actions as list or string
            for entry in doc['admin_chain']:
                if 'actions' not in entry or not isinstance(entry['actions'], (list, str)):
                    entry['actions'] = ["No actions recorded"]
                    updated = True

        if updated:
            db.collection(collection_name).document(doc_id).set(doc)
            print(f"Fixed document: {doc_id}")

# Fix both draft and finalized collections
fix_admin_chain("students_draft")
fix_admin_chain("students_final")

print("All student documents have been fixed!")

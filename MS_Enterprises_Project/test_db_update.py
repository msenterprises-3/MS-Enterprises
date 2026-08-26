import requests
import json
import uuid

def test():
    # Login as admin to get session cookie
    sess = requests.Session()
    # Mocking admin login? We don't have credentials. 
    # Let's bypass by directly invoking the python function or using the DB wrapper.
    from app import app, db
    
    with app.test_request_context():
        # Get first product
        products = db.collection('products').stream()
        p = list(products)[0].to_dict()
        p_id = list(db.collection('products').stream())[0].id
        print(f"Editing Product: {p_id}, {p.get('name')}")
        
        # Test update via db.collection directly
        try:
            db.collection('products').document(p_id).update({
                'name': p.get('name', '') + ' TEST'
            })
            print("Update via db.collection succeeded!")
            
            # Re-fetch
            doc = db.collection('products').document(p_id).get()
            print("Refetched name:", doc.to_dict().get('name'))
        except Exception as e:
            print("Error updating:", str(e))

if __name__ == '__main__':
    test()

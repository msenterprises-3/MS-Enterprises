import os
import sqlite3
import json
import uuid
from datetime import datetime

class Increment:
    """Atomic field increment representation."""
    def __init__(self, value=1):
        self.value = value

# Helper to clean ID formats between integer and string database primary keys
def clean_id(doc_id):
    if doc_id is None:
        return None
    try:
        if str(doc_id).isdigit():
            return int(doc_id)
    except Exception:
        pass
    return str(doc_id)

def map_document_data(collection_name, data):
    mapped = dict(data)
    if collection_name == 'orders':
        if 'delivery_address' in mapped:
            mapped['shipping_address'] = mapped.pop('delivery_address')
        if 'items' in mapped:
            items_data = mapped.pop('items')
            if isinstance(items_data, (list, dict)):
                mapped['items_json'] = json.dumps(items_data)
            else:
                mapped['items_json'] = str(items_data)
        if 'order_id' in mapped:
            mapped['id'] = mapped['order_id']
            
    elif collection_name == 'dealer_orders':
        if 'order_id' in mapped:
            mapped['id'] = mapped['order_id']
        if 'items' in mapped:
            items_data = mapped.pop('items')
            if isinstance(items_data, (list, dict)):
                mapped['items_json'] = json.dumps(items_data)
            else:
                mapped['items_json'] = str(items_data)
                
    elif collection_name == 'dealer_activities':
        if 'activity_id' in mapped:
            mapped['id'] = mapped['activity_id']
            
    elif collection_name == 'bulk_enquiries':
        if 'enquiry_id' in mapped:
            mapped['id'] = mapped['enquiry_id']
            
    return mapped

class SQLiteDBAdapter:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'catalogue.db')
        
    def collection(self, name):
        return LocalCollectionRef(self.db_path, name)
        
    def batch(self):
        return LocalWriteBatch(self.db_path)

# Backwards compatibility alias
SQLiteFirestoreMock = SQLiteDBAdapter

class LocalCollectionRef:
    def __init__(self, db_path, name):
        self.db_path = db_path
        self.name = name
        
    def document(self, doc_id=None):
        if doc_id is None:
            doc_id = uuid.uuid4().hex
        return LocalDocumentRef(self.db_path, self.name, doc_id)
        
    def add(self, data):
        doc_id = uuid.uuid4().hex
        doc_ref = LocalDocumentRef(self.db_path, self.name, doc_id)
        doc_ref.set(data)
        return None, doc_ref
        
    def where(self, field, op, value):
        query = LocalQuery(self.db_path, self.name)
        return query.where(field, op, value)
        
    def order_by(self, field, direction="ASCENDING"):
        query = LocalQuery(self.db_path, self.name)
        return query.order_by(field, direction)
        
    def limit(self, count):
        query = LocalQuery(self.db_path, self.name)
        return query.limit(count)
        
    def get(self):
        return LocalQuery(self.db_path, self.name).get()
        
    def stream(self):
        return LocalQuery(self.db_path, self.name).stream()
        
    def on_snapshot(self, callback):
        return None

class LocalDocumentRef:
    def __init__(self, db_path, collection_name, doc_id):
        self.db_path = db_path
        self.collection_name = collection_name
        self.raw_id = doc_id
        
        # settings document 'global' maps to row ID 1 in SQLite
        if self.collection_name == 'settings' and doc_id == 'global':
            self.id = 1
        else:
            self.id = clean_id(doc_id)
            
    def get(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check table columns to know primary key column name
        cursor.execute(f"PRAGMA table_info({self.collection_name})")
        columns = [row[1] for row in cursor.fetchall()]
        pk_col = columns[0] if columns else 'id'
        
        cursor.execute(f"SELECT * FROM {self.collection_name} WHERE {pk_col} = ?", (self.id,))
        row = cursor.fetchone()
        conn.close()
        
        return LocalDocumentSnapshot(self.collection_name, self.raw_id, row)
        
    def set(self, data, merge=False):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({self.collection_name})")
        columns = [row[1] for row in cursor.fetchall()]
        pk_col = columns[0] if columns else 'id'
        
        # Build insert fields and placeholders
        insert_data = map_document_data(self.collection_name, data)
        insert_data[pk_col] = self.id
        
        # Handle datetime serialization and JSON conversions
        for k, v in list(insert_data.items()):
            if k not in columns:
                insert_data.pop(k)  # Filter out non-existing schema columns
            elif isinstance(v, Increment):
                insert_data[k] = v.value
            elif isinstance(v, (dict, list)):
                insert_data[k] = json.dumps(v)
            elif hasattr(v, 'isoformat'):
                insert_data[k] = v.isoformat()
            elif isinstance(v, datetime):
                insert_data[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                
        fields = list(insert_data.keys())
        if not fields:
            conn.close()
            return
            
        placeholders = ', '.join(['?'] * len(fields))
        field_list = ', '.join(fields)
        
        sql = f"INSERT OR REPLACE INTO {self.collection_name} ({field_list}) VALUES ({placeholders})"
        cursor.execute(sql, [insert_data[f] for f in fields])
        
        conn.commit()
        conn.close()
        
    def update(self, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({self.collection_name})")
        columns = [row[1] for row in cursor.fetchall()]
        pk_col = columns[0] if columns else 'id'
        
        update_data = map_document_data(self.collection_name, data)
        for k, v in list(update_data.items()):
            if k not in columns:
                update_data.pop(k)
            elif isinstance(v, Increment):
                pass
            elif isinstance(v, (dict, list)):
                update_data[k] = json.dumps(v)
            elif hasattr(v, 'isoformat'):
                update_data[k] = v.isoformat()
            elif isinstance(v, datetime):
                update_data[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                
        if not update_data:
            conn.close()
            return
            
        sets_list = []
        params = []
        for k, v in update_data.items():
            if isinstance(v, Increment):
                sets_list.append(f"{k} = COALESCE({k}, 0) + ?")
                params.append(v.value)
            else:
                sets_list.append(f"{k} = ?")
                params.append(v)
                
        sets = ', '.join(sets_list)
        params.append(self.id)
        
        sql = f"UPDATE {self.collection_name} SET {sets} WHERE {pk_col} = ?"
        cursor.execute(sql, params)
        
        conn.commit()
        conn.close()
        
    def delete(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({self.collection_name})")
        columns = [row[1] for row in cursor.fetchall()]
        pk_col = columns[0] if columns else 'id'
        
        cursor.execute(f"DELETE FROM {self.collection_name} WHERE {pk_col} = ?", (self.id,))
        conn.commit()
        conn.close()

class LocalQuery:
    def __init__(self, db_path, collection_name):
        self.db_path = db_path
        self.collection_name = collection_name
        self.filters = []
        self.orders = []
        self.limit_count = None
        
    def where(self, field, op, value):
        # Convert operators
        if op == '==':
            op = '='
        self.filters.append((field, op, value))
        return self
        
    def order_by(self, field, direction="ASCENDING"):
        direction_clause = "DESC" if "DESC" in str(direction).upper() else "ASC"
        self.orders.append((field, direction_clause))
        return self
        
    def limit(self, count):
        self.limit_count = count
        return self
        
    def get(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        sql = f"SELECT * FROM {self.collection_name}"
        params = []
        
        # Build filters
        if self.filters:
            wheres = []
            for field, op, value in self.filters:
                wheres.append(f"{field} {op} ?")
                params.append(value)
            sql += " WHERE " + " AND ".join(wheres)
            
        # Build ordering
        if self.orders:
            order_clauses = [f"{field} {dir_}" for field, dir_ in self.orders]
            sql += " ORDER BY " + ", ".join(order_clauses)
            
        # Build limit
        if self.limit_count is not None:
            sql += f" LIMIT {self.limit_count}"
            
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"[LocalQuery] Query warning on {self.collection_name}: {e}")
            rows = []
            
        conn.close()
        
        return [LocalDocumentSnapshot(self.collection_name, row[0] if len(row) > 0 else '', row) for row in rows]
        
    def stream(self):
        return self.get()

class LocalDocumentSnapshot:
    def __init__(self, collection_name, doc_id, row):
        self.collection_name = collection_name
        self._id = doc_id
        self._row = row
        self.exists = row is not None
        
    @property
    def reference(self):
        return db.collection(self.collection_name).document(self._id)
        
    @property
    def id(self):
        if self.collection_name == 'settings' and self._id == 1:
            return 'global'
        return str(self._id) if self._id is not None else ''
        
    def to_dict(self):
        if not self.exists:
            return {}
            
        data = dict(self._row)
        
        # Parse JSON fields back to dicts/lists
        for k, v in list(data.items()):
            if isinstance(v, str):
                if v.startswith('{') and v.endswith('}'):
                    try:
                        data[k] = json.loads(v)
                    except Exception:
                        pass
                elif v.startswith('[') and v.endswith(']'):
                    try:
                        data[k] = json.loads(v)
                    except Exception:
                        pass
                        
        return data

class LocalWriteBatch:
    def __init__(self, db_path):
        self.db_path = db_path
        self.ops = []
        
    def set(self, doc_ref, data, merge=False):
        self.ops.append(('set', doc_ref, data))
        
    def update(self, doc_ref, data):
        self.ops.append(('update', doc_ref, data))
        
    def delete(self, doc_ref):
        self.ops.append(('delete', doc_ref, None))
        
    def commit(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            for op, doc_ref, data in self.ops:
                pk_col = 'id'
                if op == 'set':
                    insert_data = map_document_data(doc_ref.collection_name, data)
                    insert_data[pk_col] = doc_ref.id
                    cursor.execute(f"PRAGMA table_info({doc_ref.collection_name})")
                    columns = [row[1] for row in cursor.fetchall()]
                    for k, v in list(insert_data.items()):
                        if k not in columns:
                            insert_data.pop(k)
                        elif isinstance(v, Increment):
                            insert_data[k] = v.value
                        elif isinstance(v, (dict, list)):
                            insert_data[k] = json.dumps(v)
                        elif hasattr(v, 'isoformat'):
                            insert_data[k] = v.isoformat()
                        elif isinstance(v, datetime):
                            insert_data[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                            
                    fields = list(insert_data.keys())
                    if not fields:
                        continue
                    placeholders = ', '.join(['?'] * len(fields))
                    field_list = ', '.join(fields)
                    sql = f"INSERT OR REPLACE INTO {doc_ref.collection_name} ({field_list}) VALUES ({placeholders})"
                    cursor.execute(sql, [insert_data[f] for f in fields])
                    
                elif op == 'update':
                    update_data = map_document_data(doc_ref.collection_name, data)
                    cursor.execute(f"PRAGMA table_info({doc_ref.collection_name})")
                    columns = [row[1] for row in cursor.fetchall()]
                    for k, v in list(update_data.items()):
                        if k not in columns:
                            update_data.pop(k)
                        elif isinstance(v, Increment):
                            pass
                        elif isinstance(v, (dict, list)):
                            update_data[k] = json.dumps(v)
                        elif hasattr(v, 'isoformat'):
                            update_data[k] = v.isoformat()
                        elif isinstance(v, datetime):
                            update_data[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                            
                    if update_data:
                        sets_list = []
                        params = []
                        for k, v in update_data.items():
                            if isinstance(v, Increment):
                                sets_list.append(f"{k} = COALESCE({k}, 0) + ?")
                                params.append(v.value)
                            else:
                                sets_list.append(f"{k} = ?")
                                params.append(v)
                        sets = ', '.join(sets_list)
                        params.append(doc_ref.id)
                        sql = f"UPDATE {doc_ref.collection_name} SET {sets} WHERE {pk_col} = ?"
                        cursor.execute(sql, params)
                        
                elif op == 'delete':
                    cursor.execute(f"DELETE FROM {doc_ref.collection_name} WHERE {pk_col} = ?", (doc_ref.id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

# Export single global client adapter instance
db = SQLiteDBAdapter()

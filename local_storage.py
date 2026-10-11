"""
Local Storage and AWS Fallback Layer for TravelGo.
Provides seamless fallback to local SQLite storage when AWS DynamoDB/SNS credentials
are not configured or when running offline, while maintaining full compatibility
with boto3's Table interface.
"""

import os
import json
import sqlite3
import uuid
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert Decimal to int if whole number, else float
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)

def eval_condition(item, cond):
    """Evaluates boto3 Key/Attr conditions against an item dictionary."""
    if cond is None:
        return True
    op = getattr(cond, 'expression_operator', None)
    if op == 'AND':
        return all(eval_condition(item, v) for v in cond._values)
    elif op == 'OR':
        return any(eval_condition(item, v) for v in cond._values)
    elif op == 'NOT':
        return not eval_condition(item, cond._values[0])
    elif op == '=':
        attr_name = cond._values[0].name
        target_val = cond._values[1]
        item_val = item.get(attr_name)
        if item_val is None:
            return False
        return str(item_val).strip() == str(target_val).strip()
    elif op == '<>':
        attr_name = cond._values[0].name
        target_val = cond._values[1]
        item_val = item.get(attr_name)
        return str(item_val).strip() != str(target_val).strip()
    elif op == '<':
        attr_name = cond._values[0].name
        return item.get(attr_name) < cond._values[1]
    elif op == '<=':
        attr_name = cond._values[0].name
        return item.get(attr_name) <= cond._values[1]
    elif op == '>':
        attr_name = cond._values[0].name
        return item.get(attr_name) > cond._values[1]
    elif op == '>=':
        attr_name = cond._values[0].name
        return item.get(attr_name) >= cond._values[1]
    return True


class LocalTable:
    def __init__(self, db_path, table_name):
        self.db_path = db_path
        self.table_name = table_name

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def get_item(self, Key):
        with self._get_connection() as conn:
            # First try exact primary key match if single key
            for k, v in Key.items():
                cur = conn.execute(
                    "SELECT data FROM storage WHERE table_name = ? AND pkey = ?",
                    (self.table_name, str(v))
                )
                row = cur.fetchone()
                if row:
                    return {'Item': json.loads(row['data'])}

            # Multi-attribute key match across table items
            cur = conn.execute(
                "SELECT data FROM storage WHERE table_name = ?",
                (self.table_name,)
            )
            for row in cur.fetchall():
                item = json.loads(row['data'])
                if all(str(item.get(k)) == str(v) for k, v in Key.items()):
                    return {'Item': item}
            return {}

    def put_item(self, Item):
        # Determine unique key
        pkey = (
            Item.get('email')
            or Item.get('booking_id')
            or f"{Item.get('user_email', '')}#{Item.get('booking_date', '')}"
            or str(uuid.uuid4())
        )
        serialized = json.dumps(Item, cls=DecimalEncoder)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO storage (table_name, pkey, data) VALUES (?, ?, ?)",
                (self.table_name, str(pkey), serialized)
            )
            conn.commit()
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}

    def query(self, KeyConditionExpression=None, ScanIndexForward=True, **kwargs):
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT data FROM storage WHERE table_name = ?",
                (self.table_name,)
            )
            items = [json.loads(row['data']) for row in cur.fetchall()]

        matching = [item for item in items if eval_condition(item, KeyConditionExpression)]
        # Sort by booking_date if present
        matching.sort(
            key=lambda x: str(x.get('booking_date', '')),
            reverse=not ScanIndexForward
        )
        return {'Items': matching}

    def scan(self, FilterExpression=None, **kwargs):
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT data FROM storage WHERE table_name = ?",
                (self.table_name,)
            )
            items = [json.loads(row['data']) for row in cur.fetchall()]

        matching = [item for item in items if eval_condition(item, FilterExpression)]
        return {'Items': matching}

    def delete_item(self, Key):
        with self._get_connection() as conn:
            # Check if deleting by primary key directly
            for k, v in Key.items():
                conn.execute(
                    "DELETE FROM storage WHERE table_name = ? AND pkey = ?",
                    (self.table_name, str(v))
                )
            # Also check matching items by composite keys
            cur = conn.execute(
                "SELECT pkey, data FROM storage WHERE table_name = ?",
                (self.table_name,)
            )
            for row in cur.fetchall():
                item = json.loads(row['data'])
                if all(str(item.get(k)) == str(v) for k, v in Key.items()):
                    conn.execute(
                        "DELETE FROM storage WHERE table_name = ? AND pkey = ?",
                        (self.table_name, row['pkey'])
                    )
            conn.commit()
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}


class LocalDynamoDBResource:
    def __init__(self, db_path='travelgo_data.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS storage (
                    table_name TEXT NOT NULL,
                    pkey TEXT NOT NULL,
                    data TEXT NOT NULL,
                    PRIMARY KEY (table_name, pkey)
                )
            """)
            conn.commit()

    def Table(self, table_name):
        return LocalTable(self.db_path, table_name)


class LocalSNSClient:
    def publish(self, TopicArn=None, Subject='', Message='', **kwargs):
        print(f"\n[SNS NOTIFICATION SIMULATED]\nSubject: {Subject}\nMessage: {Message}\n{'-'*40}")
        return {'MessageId': str(uuid.uuid4()), 'ResponseMetadata': {'HTTPStatusCode': 200}}

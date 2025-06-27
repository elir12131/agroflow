# agroflow/database.py

import sqlite3
import hashlib
import csv
import os
from datetime import datetime, timedelta

DB_FILE = os.path.join("data", "agroflow.db")
DB_FOLDER = "data"

class Database:
    def __init__(self):
        os.makedirs(DB_FOLDER, exist_ok=True)
        self.conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _create_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT, phone TEXT, address TEXT, notes TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, master_price REAL NOT NULL, category TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL, order_date TIMESTAMP NOT NULL, status TEXT NOT NULL, total_invoice REAL, FOREIGN KEY (customer_id) REFERENCES customers (id))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS order_items (id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL, product_id INTEGER NOT NULL, quantity INTEGER NOT NULL, final_price REAL, is_out_of_stock INTEGER DEFAULT 0, FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE, FOREIGN KEY (product_id) REFERENCES products (id))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        self.conn.commit()
        self._initialize_defaults()
    def _initialize_defaults(self):
        self.cursor.execute("SELECT * FROM users WHERE username='admin'")
        if not self.cursor.fetchone(): self.add_user('admin', 'admin')
        self.cursor.execute("SELECT * FROM settings WHERE key='theme'")
        if not self.cursor.fetchone(): self.set_setting('theme', 'System')

    def add_user(self, username, password):
        password_hash = self._hash_password(password)
        try:
            self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError: return False

    def verify_user(self, username, password):
        password_hash = self._hash_password(password)
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, password_hash))
        return self.cursor.fetchone()

    def update_username(self, user_id, new_username):
        try:
            self.cursor.execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))
            self.conn.commit()
            return True, "Username updated successfully."
        except sqlite3.IntegrityError:
            return False, "This username is already taken."

    def update_password(self, user_id, new_password):
        new_hash = self._hash_password(new_password)
        self.cursor.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
        self.conn.commit()
        return True, "Password updated successfully."

    def get_customers(self, search_term=""):
        if search_term: return self.conn.execute("SELECT * FROM customers WHERE name LIKE ? ORDER BY name", (f"%{search_term}%",)).fetchall()
        return self.conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    def get_products(self, search_term=""):
        if search_term: return self.conn.execute("SELECT * FROM products WHERE name LIKE ? ORDER BY name", (f"%{search_term}%",)).fetchall()
        return self.conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    def create_order(self, customer_id, cart):
        self.cursor.execute("INSERT INTO orders (customer_id, order_date, status) VALUES (?, ?, ?)", (customer_id, datetime.now(), "Pending Vendor"))
        order_id = self.cursor.lastrowid
        order_items = [(order_id, pid, data['quantity']) for pid, data in cart.items()]
        self.cursor.executemany("INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)", order_items)
        self.conn.commit(); return order_id
    def get_all_orders_with_details(self, customer_search=""):
        query = "SELECT o.id, c.name, o.order_date, o.status, o.total_invoice FROM orders o JOIN customers c ON o.customer_id = c.id"
        params = []
        if customer_search: query += " WHERE c.name LIKE ?"; params.append(f"%{customer_search}%")
        query += " ORDER BY o.order_date DESC"
        return self.conn.execute(query, tuple(params)).fetchall()
    def get_full_order_details(self, order_id):
        order_info = self.conn.execute("SELECT o.id, o.order_date, o.status, o.total_invoice, c.* FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.id = ?", (order_id,)).fetchone()
        items_info = self.conn.execute("SELECT p.name, oi.quantity, oi.final_price, oi.is_out_of_stock FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = ? AND oi.is_out_of_stock = 0", (order_id,)).fetchall()
        return order_info, items_info
    
    def get_sales_report_for_customer(self, customer_id):
        return self.conn.execute("SELECT o.id, o.order_date, o.total_invoice FROM orders o WHERE o.customer_id = ? AND o.status = 'Completed' ORDER BY o.order_date DESC", (customer_id,)).fetchall()
        
    def _execute_crud(self, query, params=()): self.cursor.execute(query, params); self.conn.commit()
    def add_customer(self, name, email, phone, address, notes): self._execute_crud("INSERT INTO customers (name, email, phone, address, notes) VALUES (?, ?, ?, ?, ?)", (name, email, phone, address, notes))
    def update_customer(self, cust_id, name, email, phone, address, notes): self._execute_crud("UPDATE customers SET name=?, email=?, phone=?, address=?, notes=? WHERE id=?", (name, email, phone, address, notes, cust_id))
    def delete_customer(self, cust_id): self._execute_crud("DELETE FROM customers WHERE id=?", (cust_id,))
    def add_product(self, name, master_price, category): self._execute_crud("INSERT INTO products (name, master_price, category) VALUES (?, ?, ?)", (name, master_price, category))
    def update_product(self, prod_id, name, master_price, category): self._execute_crud("UPDATE products SET name=?, master_price=?, category=? WHERE id=?", (name, master_price, category, prod_id))
    def delete_product(self, prod_id): self._execute_crud("DELETE FROM products WHERE id=?", (prod_id,))
    def get_order_items(self, order_id): return self.conn.execute("SELECT oi.id, p.name, oi.quantity FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = ?", (order_id,)).fetchall()
    def update_order_fulfillment(self, fulfillment_data):
        total_invoice, order_id = 0, None
        for item_id, data in fulfillment_data.items():
            if order_id is None: order_id = self.conn.execute("SELECT order_id FROM order_items WHERE id=?", (item_id,)).fetchone()[0]
            final_price = data['price'] if not data['out_of_stock'] else 0; is_out_of_stock = 1 if data['out_of_stock'] else 0
            self._execute_crud("UPDATE order_items SET final_price=?, is_out_of_stock=? WHERE id=?", (final_price, is_out_of_stock, item_id))
            if not is_out_of_stock: total_invoice += float(final_price) * int(self.conn.execute("SELECT quantity FROM order_items WHERE id=?", (item_id,)).fetchone()[0])
        if order_id: self._execute_crud("UPDATE orders SET status='Completed', total_invoice=? WHERE id=?", (total_invoice, order_id))
    def get_total_sales(self, period):
        end_date = datetime.now()
        if period == 'month': start_date = end_date - timedelta(days=30)
        elif period == 'week': start_date = end_date - timedelta(days=7)
        else: start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.conn.execute("SELECT SUM(total_invoice) FROM orders WHERE status='Completed' AND order_date BETWEEN ? AND ?", (start_date, end_date)).fetchone()
    def get_top_selling_products(self, limit=5): return self.conn.execute("SELECT p.name, SUM(oi.quantity) as total_quantity FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.is_out_of_stock = 0 GROUP BY p.name ORDER BY total_quantity DESC LIMIT ?", (limit,)).fetchall()
    def get_top_customers_by_value(self, limit=5): return self.conn.execute("SELECT c.name, SUM(o.total_invoice) as total_spent FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = 'Completed' GROUP BY c.name ORDER BY total_spent DESC LIMIT ?", (limit,)).fetchall()
    def get_setting(self, key): result = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone(); return result[0] if result else None
    def set_setting(self, key, value): self._execute_crud("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    def import_from_csv(self, file_path, table_name):
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = [tuple(row.get(col, None) for col in reader.fieldnames) for row in reader]
            if not data: return
            placeholders = ', '.join(['?'] * len(reader.fieldnames)); cols = ', '.join(reader.fieldnames)
            query = f"INSERT OR IGNORE INTO {table_name} ({cols}) VALUES ({placeholders})"
            self.cursor.executemany(query, data); self.conn.commit()
    def close(self): self.conn.close()
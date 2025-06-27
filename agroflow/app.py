# agroflow/app.py

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageOps, ImageDraw
import os
from database import Database
from datetime import datetime
import re

# --- Constants ---
APP_NAME = "AgroFlow"
WIDTH = 1366
HEIGHT = 768
SIDEBAR_WIDTH = 240

# --- Asset Paths ---
ASSETS_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets")
LOGO_PATH = os.path.join(ASSETS_PATH, "logo.png")
ICON_PROFILE_PATH = os.path.join(ASSETS_PATH, "icons", "profile.png")
ICON_DASHBOARD_PATH = os.path.join(ASSETS_PATH, "icons", "dashboard.png")
ICON_ORDERS_PATH = os.path.join(ASSETS_PATH, "icons", "orders.png")
ICON_ALL_ORDERS_PATH = os.path.join(ASSETS_PATH, "icons", "all_orders.png")
ICON_CUSTOMERS_PATH = os.path.join(ASSETS_PATH, "icons", "customers.png")
ICON_INVENTORY_PATH = os.path.join(ASSETS_PATH, "icons", "inventory.png")
ICON_REPORTS_PATH = os.path.join(ASSETS_PATH, "icons", "reports.png")
ICON_SETTINGS_PATH = os.path.join(ASSETS_PATH, "icons", "settings.png")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        try:
            ctk.set_default_color_theme("light_theme.json")
            self.THEME_NAME = "Light (Custom)"
        except Exception as e:
            print(f"Warning: Could not load 'light_theme.json'. Using default theme. Error: {e}")
            ctk.set_default_color_theme("blue")
            self.THEME_NAME = "System"

        self.db = Database()
        ctk.set_appearance_mode("Light")
        self.title(APP_NAME)
        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.minsize(1280, 720)
        
        self.current_user = None
        self._main_ui_created = False
        self.user_menu = None
        self.login_frame = LoginFrame(self)
        self.login_frame.pack(expand=True, fill="both")
        self.bind("<Button-1>", self.handle_global_click)

    def show_main_app(self, user):
        self.current_user = user
        self.withdraw()
        self.login_frame.pack_forget()
        if not self._main_ui_created:
            self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
            self.sidebar_frame = ctk.CTkFrame(self, width=SIDEBAR_WIDTH, corner_radius=0)
            self.sidebar_frame.grid(row=0, column=0, sticky="nsw")
            self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
            self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            self.main_frame.grid_columnconfigure(0, weight=1); self.main_frame.grid_rowconfigure(0, weight=1)
            
            # Create all frames
            self.frames = {}
            frame_classes = [DashboardFrame, OrderFrame, AllOrdersFrame, CustomersFrame, InventoryFrame, ReportsFrame, SettingsFrame, AccountManagementFrame]
            for F in frame_classes:
                page_name = F.__name__
                frame = F(self.main_frame, self, self.db)
                self.frames[page_name] = frame
                frame.grid(row=0, column=0, sticky="nsew")

            self._main_ui_created = True
        
        # Always recreate sidebar in case user info changed
        self._create_sidebar()
        self.select_frame("DashboardFrame")
        self.deiconify()

    def _create_sidebar(self):
        for widget in self.sidebar_frame.winfo_children(): widget.destroy()
        
        ctk.CTkLabel(self.sidebar_frame, text=APP_NAME, font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold")).pack(pady=(20, 20), padx=20)
        
        button_info = [("Dashboard", ICON_DASHBOARD_PATH, "DashboardFrame"), ("New Order", ICON_ORDERS_PATH, "OrderFrame"), ("All Orders", ICON_ALL_ORDERS_PATH, "AllOrdersFrame"), ("Customers", ICON_CUSTOMERS_PATH, "CustomersFrame"), ("Inventory", ICON_INVENTORY_PATH, "InventoryFrame"), ("Reports", ICON_REPORTS_PATH, "ReportsFrame")]
        self.nav_buttons = {}
        for text, icon_path, frame_name in button_info:
            try: icon = ctk.CTkImage(Image.open(icon_path), size=(20, 20))
            except: icon = None
            button = ctk.CTkButton(self.sidebar_frame, text=text, image=icon, anchor="w", height=40, border_spacing=10, fg_color="transparent", hover=False, command=lambda fn=frame_name: self.select_frame(fn))
            button.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[frame_name] = button
            ctk.CTkFrame(self.sidebar_frame, height=1, fg_color="#E0E0E0").pack(fill="x", padx=20)
            
        bottom_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent"); bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10); bottom_frame.grid_columnconfigure(1, weight=1)
        self.profile_button = ctk.CTkButton(bottom_frame, text=self.current_user['username'], height=32, fg_color="transparent", hover=False, command=self.show_user_menu)
        try:
            profile_image = Image.open(ICON_PROFILE_PATH).resize((24, 24), Image.Resampling.LANCZOS); mask = Image.new('L', (24, 24), 0); draw = ImageDraw.Draw(mask); draw.ellipse((0, 0, 24, 24), fill=255); profile_image.putalpha(mask)
            self.profile_button.configure(image=ctk.CTkImage(profile_image, size=(24, 24)))
        except Exception as e: print(f"Warning: Profile icon missing '{ICON_PROFILE_PATH}'. Error: {e}")
        self.profile_button.grid(row=0, column=1, sticky="ew", padx=(10,0))
        try:
            settings_icon = ctk.CTkImage(Image.open(ICON_SETTINGS_PATH), size=(20, 20))
            self.settings_button = ctk.CTkButton(bottom_frame, text="", image=settings_icon, width=32, height=32, fg_color="transparent", hover=False, command=lambda: self.select_frame("SettingsFrame"))
            self.settings_button.grid(row=0, column=0)
        except: self.settings_button = ctk.CTkButton(bottom_frame, text="Settings", command=lambda: self.select_frame("SettingsFrame")); self.settings_button.grid(row=0, column=0)

    def show_user_menu(self):
        if self.user_menu and self.user_menu.winfo_exists(): self.user_menu.destroy(); self.user_menu = None; return
        x, y, height = self.profile_button.winfo_rootx(), self.profile_button.winfo_rooty(), self.profile_button.winfo_height()
        self.user_menu = ctk.CTkToplevel(self); self.user_menu.overrideredirect(True); self.user_menu.geometry(f"180x80+{x-90}+{y - 85}")
        ctk.CTkButton(self.user_menu, text="Account Management", command=lambda: self.select_frame_and_close_menu("AccountManagementFrame")).pack(expand=True, fill="both", padx=5, pady=(5,2))
        ctk.CTkButton(self.user_menu, text="Logout", fg_color="#D32F2F", hover_color="#B71C1C", command=self.logout).pack(expand=True, fill="both", padx=5, pady=(2,5))
        self.user_menu.focus_set()

    def handle_global_click(self, event):
        if self.user_menu and self.user_menu.winfo_exists():
            if not (self.user_menu.winfo_rootx() <= event.x_root <= self.user_menu.winfo_rootx() + self.user_menu.winfo_width() and self.user_menu.winfo_rooty() <= event.y_root <= self.user_menu.winfo_rooty() + self.user_menu.winfo_height()):
                self.user_menu.destroy(); self.user_menu = None

    def select_frame_and_close_menu(self, frame_name):
        if self.user_menu: self.user_menu.destroy(); self.user_menu = None
        self.select_frame(frame_name)

    def select_frame(self, page_name):
        hover_color, transparent_color = ("#E5E5E5", "#3D3D3D"), "transparent"
        for name, button in self.nav_buttons.items(): button.configure(fg_color=hover_color if name == page_name else transparent_color)
        if hasattr(self, 'settings_button'): self.settings_button.configure(fg_color=hover_color if page_name == "SettingsFrame" else transparent_color)
        if page_name not in self.nav_buttons and page_name != "SettingsFrame": [btn.configure(fg_color=transparent_color) for btn in self.nav_buttons.values()]
        for frame in self.frames.values(): frame.grid_remove()
        frame_to_show = self.frames[page_name]; frame_to_show.grid()
        if hasattr(frame_to_show, 'refresh_data'): frame_to_show.refresh_data()
    
    def logout(self):
        if self.user_menu: self.user_menu.destroy()
        self.current_user = None
        for widget in self.winfo_children():
            if widget is not self.login_frame: widget.destroy()
        self._main_ui_created = False; self.login_frame.pack(expand=True, fill="both"); self.login_frame.clear_fields()
        self.withdraw(); self.deiconify()

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master); self.master = master
        content_frame = ctk.CTkFrame(self, width=360, corner_radius=15); content_frame.place(relx=0.5, rely=0.5, anchor="center")
        try: ctk.CTkLabel(content_frame, image=ctk.CTkImage(Image.open(LOGO_PATH), size=(180, 60)), text="").pack(pady=(40, 20))
        except: ctk.CTkLabel(content_frame, text=APP_NAME, font=ctk.CTkFont(size=30, weight="bold")).pack(pady=(40, 20))
        self.username_entry = ctk.CTkEntry(content_frame, width=250, placeholder_text="Username"); self.username_entry.pack(pady=10, padx=30); self.username_entry.bind("<Return>", self.login_event)
        self.password_entry = ctk.CTkEntry(content_frame, width=250, placeholder_text="Password", show="*"); self.password_entry.pack(pady=10, padx=30); self.password_entry.bind("<Return>", self.login_event)
        ctk.CTkButton(content_frame, text="Login", width=250, command=self.login_event).pack(pady=20, padx=30)
        self.error_label = ctk.CTkLabel(content_frame, text="", text_color="#D32F2F"); self.error_label.pack(pady=(0, 20))
    def login_event(self, event=None):
        user = self.master.db.verify_user(self.username_entry.get(), self.password_entry.get())
        if user: self.error_label.configure(text=""); self.master.show_main_app(user)
        else: self.error_label.configure(text="Invalid username or password")
    def clear_fields(self): self.username_entry.delete(0, 'end'); self.password_entry.delete(0, 'end'); self.error_label.configure(text=""); self.username_entry.focus()
class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance, db):
        super().__init__(master, fg_color="transparent"); self.app, self.db = app_instance, db; self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        self.welcome_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=32, weight="bold")); self.welcome_label.grid(row=0, column=0, sticky="w", padx=20, pady=20)
        actions_container = ctk.CTkFrame(self, fg_color="transparent"); actions_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10); actions_container.grid_columnconfigure((0, 1, 2), weight=1)
        self.create_action_card(actions_container, 0, "New Order", "Start a new customer order.", "OrderFrame")
        self.create_action_card(actions_container, 1, "View All Orders", "Browse and manage past orders.", "AllOrdersFrame")
        self.create_action_card(actions_container, 2, "AI & Manual Reports", "Get business insights.", "ReportsFrame")
    def create_action_card(self, parent, column, title, description, frame_name):
        card = ctk.CTkFrame(parent, border_width=1); card.grid(row=0, column=column, sticky="nsew", padx=10, pady=10); card.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 5), padx=15)
        ctk.CTkLabel(card, text=description, wraplength=200).pack(pady=5, padx=15)
        ctk.CTkButton(card, text=f"Go to {title}", command=lambda: self.app.select_frame(frame_name)).pack(pady=15, padx=15)
    def refresh_data(self): self.welcome_label.configure(text=f"Welcome, {self.app.current_user['username'].capitalize()}!")
class Dropdown(ctk.CTkToplevel):
    def __init__(self, parent_entry, results, callback):
        super().__init__(parent_entry); self.overrideredirect(True); self.callback = callback
        x, y, width = parent_entry.winfo_rootx(), parent_entry.winfo_rooty() + parent_entry.winfo_height(), parent_entry.winfo_width()
        self.geometry(f"{width}x{min(200, len(results)*35)}"+f"+{x}+{y}")
        scroll_frame = ctk.CTkScrollableFrame(self); scroll_frame.pack(expand=True, fill="both")
        for result in results: ctk.CTkButton(scroll_frame, text=result['name'], anchor="w", fg_color="transparent", hover=False, command=lambda r=result: self.select(r)).pack(fill="x")
        self.bind("<FocusOut>", lambda e: self.destroy()); self.focus_set()
    def select(self, result): self.callback(result); self.destroy()
class OrderFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance, db):
        super().__init__(master, fg_color="transparent"); self.app, self.db = app_instance, db; self.cart, self.current_customer_id, self.last_submitted_order_id, self.dropdown = {}, None, None, None
        self.grid_columnconfigure(0, weight=2); self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        left_panel = ctk.CTkFrame(self); left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10)); left_panel.grid_rowconfigure(1, weight=1); left_panel.grid_columnconfigure(0, weight=1)
        selection_area = ctk.CTkScrollableFrame(left_panel, label_text="Order Details"); selection_area.grid(row=0, column=0, sticky="nsew", pady=10); selection_area.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(selection_area, text="Customer").pack(anchor="w", padx=5); self.customer_entry = ctk.CTkEntry(selection_area, placeholder_text="Start typing to search..."); self.customer_entry.pack(fill="x", padx=5, pady=(0,10)); self.customer_entry.bind("<KeyRelease>", self.filter_customers); self.customer_entry.bind("<FocusOut>", lambda e: self.after(150, self.close_dropdown))
        ctk.CTkLabel(selection_area, text="Products").pack(anchor="w", padx=5); self.product_search_entry = ctk.CTkEntry(selection_area, placeholder_text="Search for products..."); self.product_search_entry.pack(fill="x", padx=5, pady=(0,10)); self.product_search_entry.bind("<KeyRelease>", self.filter_products)
        self.product_list_frame = ctk.CTkFrame(selection_area, fg_color="transparent"); self.product_list_frame.pack(expand=True, fill="both")
        right_panel = ctk.CTkFrame(self); right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0)); right_panel.grid_rowconfigure(1, weight=1); right_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(right_panel, text="Current Order", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=10, padx=10)
        self.cart_items_frame = ctk.CTkScrollableFrame(right_panel); self.cart_items_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        actions_frame = ctk.CTkFrame(right_panel, fg_color="transparent"); actions_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10); actions_frame.grid_columnconfigure((0, 1), weight=1)
        self.submit_order_button = ctk.CTkButton(actions_frame, text="Submit Order", state="disabled", command=self.submit_order); self.submit_order_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.send_vendor_button = ctk.CTkButton(actions_frame, text="Send to Vendor", state="disabled", command=self.send_to_vendor); self.send_vendor_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.print_invoice_button = ctk.CTkButton(actions_frame, text="Print Invoice", state="disabled", command=self.print_invoice); self.print_invoice_button.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(10,0))
        self.email_invoice_button = ctk.CTkButton(actions_frame, text="Email Invoice", state="disabled", command=self.email_invoice); self.email_invoice_button.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(10,0))
    def filter_customers(self, event=None):
        self.close_dropdown(); search_term = self.customer_entry.get()
        if not search_term: return
        customers = self.db.get_customers(search_term)
        if customers: self.dropdown = Dropdown(self.customer_entry, customers, self.on_customer_select)
    def close_dropdown(self):
        if self.dropdown and self.dropdown.winfo_exists(): self.dropdown.destroy(); self.dropdown = None
    def on_customer_select(self, customer): self.current_customer_id = customer['id']; self.customer_entry.delete(0, "end"); self.customer_entry.insert(0, customer['name']); self.close_dropdown(); self.update_actions_state()
    def update_actions_state(self):
        self.submit_order_button.configure(state="normal" if self.cart and self.current_customer_id else "disabled"); can_invoice = False
        if self.last_submitted_order_id:
             order_info, _ = self.db.get_full_order_details(self.last_submitted_order_id)
             if order_info and order_info['status'] == 'Completed': can_invoice = True
        self.print_invoice_button.configure(state="normal" if can_invoice else "disabled"); self.email_invoice_button.configure(state="normal" if can_invoice else "disabled")
    def submit_order(self): self.last_submitted_order_id = self.db.create_order(self.current_customer_id, self.cart); messagebox.showinfo("Success", f"Order #{self.last_submitted_order_id} has been created."); self.send_vendor_button.configure(state="normal", text=f"Send Order #{self.last_submitted_order_id}"); self.submit_order_button.configure(state="disabled"); self.reset_order_form()
    def reset_order_form(self): self.cart = {}; self.customer_entry.delete(0, "end"); self.current_customer_id = None; self.update_cart_display()
    def send_to_vendor(self):
        if self.last_submitted_order_id:
            win = VendorFulfillmentWindow(self, self.db, self.last_submitted_order_id); self.wait_window(win)
            self.send_vendor_button.configure(state="disabled", text="Send to Vendor"); self.update_actions_state()
    def print_invoice(self): messagebox.showinfo("Not Implemented", f"This would print a PDF for Order #{self.last_submitted_order_id}.")
    def email_invoice(self): messagebox.showinfo("Not Implemented", f"This would email the invoice for Order #{self.last_submitted_order_id}.")
    def refresh_data(self): self.filter_products(); self.reset_order_form(); self.last_submitted_order_id = None; self.update_actions_state()
    def filter_products(self, event=None):
        products = self.db.get_products(self.product_search_entry.get()); [widget.destroy() for widget in self.product_list_frame.winfo_children()]
        for product in products:
            frame = ctk.CTkFrame(self.product_list_frame); frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text=f"{product['name']} (${product['master_price']:.2f})").pack(side="left", padx=5)
            ctk.CTkButton(frame, text="Add", width=60, command=lambda p=product: self.add_to_cart(p)).pack(side="right", padx=5)
    def add_to_cart(self, product):
        prod_id = product['id']
        if prod_id in self.cart: self.cart[prod_id]['quantity'] += 1
        else: self.cart[prod_id] = {'name': product['name'], 'price': product['master_price'], 'quantity': 1}
        self.update_cart_display()
    def remove_from_cart(self, prod_id):
        if prod_id in self.cart:
            self.cart[prod_id]['quantity'] -= 1
            if self.cart[prod_id]['quantity'] == 0: del self.cart[prod_id]
        self.update_cart_display()
    def update_cart_display(self):
        [widget.destroy() for widget in self.cart_items_frame.winfo_children()]
        if not self.cart: ctk.CTkLabel(self.cart_items_frame, text="Cart is empty").pack(pady=20)
        else:
            for prod_id, data in self.cart.items():
                frame = ctk.CTkFrame(self.cart_items_frame); frame.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(frame, text=f"{data['name']} (x{data['quantity']})").pack(side="left", padx=5)
                ctk.CTkButton(frame, text="-", width=30, fg_color="#D32F2F", hover_color="#B71C1C", command=lambda p=prod_id: self.remove_from_cart(p)).pack(side="right", padx=5)
        self.update_actions_state()
class ReportsFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance, db):
        super().__init__(master, fg_color="transparent"); self.app, self.db = app_instance, db; self.grid_columnconfigure((0, 1), weight=1); self.grid_rowconfigure(0, weight=1)
        chat_container = ctk.CTkFrame(self, border_width=1); chat_container.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=10); chat_container.grid_rowconfigure(1, weight=1); chat_container.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(chat_container, text="AI Assistant", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.chat_frame = ctk.CTkScrollableFrame(chat_container); self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        input_frame = ctk.CTkFrame(chat_container, fg_color="transparent"); input_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5); input_frame.grid_columnconfigure(0, weight=1)
        self.user_input = ctk.CTkEntry(input_frame, placeholder_text="Ask me anything..."); self.user_input.grid(row=0, column=0, sticky="ew", padx=(0, 10)); self.user_input.bind("<Return>", self.send_message)
        ctk.CTkButton(input_frame, text="Ask", command=self.send_message).grid(row=0, column=1)
        manual_container = ctk.CTkFrame(self, border_width=1); manual_container.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=10); manual_container.grid_rowconfigure(2, weight=1); manual_container.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(manual_container, text="Manual Reports", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(manual_container, text="Select Customer:").pack(padx=10, anchor="w")
        self.report_customer_combo = ctk.CTkComboBox(manual_container, values=[], command=self.generate_report); self.report_customer_combo.pack(fill="x", padx=10, pady=5)
        self.report_display = ctk.CTkTextbox(manual_container, state="disabled", wrap="word"); self.report_display.pack(expand=True, fill="both", padx=10, pady=10)
        self.after(100, lambda: self.add_message("AI", "Hello! How can I help you today?"))
    def add_message(self, sender, message):
        is_user = sender == "You"; bubble_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        if is_user:
            bubble_container.pack(anchor="e", padx=(50, 5), pady=5)
            ctk.CTkLabel(bubble_container, text=message, wraplength=300, fg_color="#36719F", text_color="white", corner_radius=15, justify="left").pack(ipadx=10, ipady=5)
        else:
            bubble_container.pack(anchor="w", padx=(5, 50), pady=5)
            ctk.CTkLabel(bubble_container, text=message, wraplength=300, fg_color="#E5E5E5", text_color="#1A1A1A", corner_radius=15, justify="left").pack(ipadx=10, ipady=5)
        self.after(100, self.chat_frame._parent_canvas.yview_moveto, 1.0)
    def send_message(self, event=None): query = self.user_input.get(); self.add_message("You", query); self.user_input.delete(0, "end"); self.process_ai_query(query.lower())
    def process_ai_query(self, query):
        if any(word in query for word in ["hello", "hi", "hey"]): response = "Hi there! What report can I get for you?"
        elif any(word in query for word in ["thank", "thanks"]): response = "You're welcome! Is there anything else?"
        elif "total sales" in query:
            period = 'month';
            if 'week' in query: period = 'week'
            if 'day' in query or 'today' in query: period = 'day'
            total = self.db.get_total_sales(period); response = f"Total sales for the last {period} were ${total[0]:.2f}." if total and total[0] is not None else f"No sales in the last {period}."
        elif "top" in query and "product" in query:
            limit = int(re.search(r'(\d+)', query).group(1)) if re.search(r'(\d+)', query) else 5; products = self.db.get_top_selling_products(limit)
            if products: response = f"Top {len(products)} products:\n" + "\n".join([f"- {p['name']} ({p['total_quantity']} units)" for p in products])
            else: response = "No product sales data found."
        elif "top" in query and "customer" in query:
            limit = int(re.search(r'(\d+)', query).group(1)) if re.search(r'(\d+)', query) else 5; customers = self.db.get_top_customers_by_value(limit)
            if customers: response = f"Top {len(customers)} customers:\n" + "\n".join([f"- {c['name']} (${c['total_spent']:.2f})" for c in customers])
            else: response = "No customer sales data found."
        else: response = "I can help with sales totals, top products, and top customers. How can I assist?"
        self.add_message("AI", response)
    def generate_report(self, selected_name):
        customer_id = self.customer_map.get(selected_name); self.report_display.configure(state="normal"); self.report_display.delete("1.0", "end")
        if not customer_id: self.report_display.insert("1.0", "Please select a valid customer."); self.report_display.configure(state="disabled"); return
        orders = self.db.get_sales_report_for_customer(customer_id)
        if not orders: self.report_display.insert("1.0", f"No completed orders found for {selected_name}.")
        else:
            report_text = f"Sales Report for: {selected_name}\n" + "="*30 + "\n"; total_value = 0
            for order in orders: report_text += f"Order #{order['id']} on {order['order_date'].strftime('%Y-%m-%d')} - Total: ${order['total_invoice']:.2f}\n"; total_value += order['total_invoice']
            report_text += "="*30 + f"\nTotal Value: ${total_value:.2f}"; self.report_display.insert("1.0", report_text)
        self.report_display.configure(state="disabled")
    def refresh_data(self): customers = self.db.get_customers(); self.customer_map = {c['name']: c['id'] for c in customers}; self.report_customer_combo.configure(values=list(self.customer_map.keys())); self.report_customer_combo.set("Select a customer..."); self.report_display.configure(state="normal"); self.report_display.delete("1.0", "end"); self.report_display.configure(state="disabled")
class AccountManagementFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance, db):
        super().__init__(master, fg_color="transparent"); self.app, self.db = app_instance, db
        container = ctk.CTkFrame(self); container.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(container, text="Account Management", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20, padx=40)
        ctk.CTkLabel(container, text="Change Username", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.username_entry = ctk.CTkEntry(container, width=300); self.username_entry.pack(pady=(5, 10), padx=20)
        ctk.CTkButton(container, text="Update Username", command=self.update_username).pack(pady=5, padx=20)
        ctk.CTkLabel(container, text="Change Password", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(20,0))
        self.new_pass_entry = ctk.CTkEntry(container, placeholder_text="New Password", width=300, show="*"); self.new_pass_entry.pack(pady=5, padx=20)
        self.confirm_pass_entry = ctk.CTkEntry(container, placeholder_text="Confirm New Password", width=300, show="*"); self.confirm_pass_entry.pack(pady=5, padx=20)
        ctk.CTkButton(container, text="Update Password", command=self.update_password).pack(pady=(5, 20), padx=20)
    def update_username(self):
        new_username = self.username_entry.get()
        if not new_username: messagebox.showerror("Error", "Username cannot be empty."); return
        success, msg = self.db.update_username(self.app.current_user['id'], new_username)
        if success: messagebox.showinfo("Success", msg); self.app.logout()
        else: messagebox.showerror("Error", msg)
    def update_password(self):
        new_pass, confirm_pass = self.new_pass_entry.get(), self.confirm_pass_entry.get()
        if not new_pass or len(new_pass) < 4: messagebox.showerror("Error", "Password must be at least 4 characters."); return
        if new_pass != confirm_pass: messagebox.showerror("Error", "Passwords do not match."); return
        success, msg = self.db.update_password(self.app.current_user['id'], new_pass); messagebox.showinfo("Success", msg); self.app.logout()
    def refresh_data(self): self.username_entry.delete(0, "end"); self.username_entry.insert(0, self.app.current_user['username']); self.new_pass_entry.delete(0, "end"); self.confirm_pass_entry.delete(0, "end")
class AllOrdersFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance, db):
        super().__init__(master, fg_color="transparent"); self.app, self.db, self.selected_order_id = app_instance, db, None; self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(1, weight=1); search_frame = ctk.CTkFrame(self, fg_color="transparent"); search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10); self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search by customer name..."); self.search_entry.pack(fill="x"); self.search_entry.bind("<KeyRelease>", self.filter_orders); self.order_list_frame = ctk.CTkScrollableFrame(self, label_text="All Orders"); self.order_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10); self.details_frame = ctk.CTkFrame(self); self.details_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10); self.details_frame.grid_columnconfigure((0,1), weight=1); self.details_frame.grid_rowconfigure(1, weight=1); ctk.CTkLabel(self.details_frame, text="Order Details", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=10, padx=10, sticky="w"); self.details_text = ctk.CTkTextbox(self.details_frame, state="disabled", wrap="word"); self.details_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10); self.print_button = ctk.CTkButton(self.details_frame, text="Print Invoice", state="disabled", command=self.print_invoice); self.print_button.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10)); self.email_button = ctk.CTkButton(self.details_frame, text="Email Invoice", state="disabled", command=self.email_invoice); self.email_button.grid(row=2, column=1, sticky="ew", padx=10, pady=(0, 10))
    def refresh_data(self): self.filter_orders(); self.clear_details()
    def filter_orders(self, event=None):
        orders = self.db.get_all_orders_with_details(self.search_entry.get()); [widget.destroy() for widget in self.order_list_frame.winfo_children()]
        for order in orders: ctk.CTkButton(self.order_list_frame, text=f"#{order['id']} - {order['name']} ({order['order_date'].strftime('%Y-%m-%d')}) - {order['status']} - ${order['total_invoice']:.2f}" if order['total_invoice'] is not None else "N/A", anchor="w", command=lambda o=order: self.select_order(o)).pack(fill="x", pady=2)
    def select_order(self, order):
        self.selected_order_id = order['id']; order_details, item_details = self.db.get_full_order_details(self.selected_order_id)
        if not order_details: return
        total, date = (f"${order_details['total_invoice']:.2f}" if order_details['total_invoice'] is not None else "Pending"), order_details['order_date'].strftime('%Y-%m-%d %H:%M'); details_str = f"Order ID: #{order_details['id']}\nCustomer: {order_details['name']}\nDate: {date}\nStatus: {order_details['status']}\nTotal: {total}\n\n--- Items ---\n" + "".join([f"- {item['name']} (x{item['quantity']}) @ ${item['final_price']:.2f}\n" for item in item_details]); self.details_text.configure(state="normal"); self.details_text.delete("1.0", "end"); self.details_text.insert("1.0", details_str); self.details_text.configure(state="disabled")
        if order_details['status'] == 'Completed': self.print_button.configure(state="normal"); self.email_button.configure(state="normal")
        else: self.print_button.configure(state="disabled"); self.email_button.configure(state="disabled")
    def clear_details(self): self.selected_order_id = None; self.details_text.configure(state="normal"); self.details_text.delete("1.0", "end"); self.details_text.insert("1.0", "Select an order to see details."); self.details_text.configure(state="disabled"); self.print_button.configure(state="disabled"); self.email_button.configure(state="disabled")
    def print_invoice(self): messagebox.showinfo("Not Implemented", f"This would print a PDF for Order #{self.selected_order_id}.")
    def email_invoice(self): messagebox.showinfo("Not Implemented", f"This would email the invoice for Order #{self.selected_order_id}.")
class BaseCrudFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance, db, title, item_name, fields, db_get_all, db_add, db_update, db_delete, db_search, db_import):
        super().__init__(master, fg_color="transparent"); self.app, self.db, self.title, self.item_name, self.fields = app_instance, db, title, item_name, fields; self.db_get_all, self.db_add, self.db_update, self.db_delete, self.db_search, self.db_import = db_get_all, db_add, db_update, db_delete, db_search, db_import; self.selected_item_id = None; self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=2); self.grid_rowconfigure(0, weight=1); left_panel = ctk.CTkFrame(self); left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10)); left_panel.grid_rowconfigure(2, weight=1); left_panel.grid_columnconfigure(0, weight=1); ctk.CTkLabel(left_panel, text=self.title, font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=10, padx=10, sticky="w"); self.search_entry = ctk.CTkEntry(left_panel, placeholder_text=f"Search {item_name}s..."); self.search_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10)); self.search_entry.bind("<KeyRelease>", self.filter_list); self.item_list_frame = ctk.CTkScrollableFrame(left_panel); self.item_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10)); right_panel = ctk.CTkFrame(self); right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0)); right_panel.grid_columnconfigure(0, weight=1); right_panel.grid_rowconfigure(0, weight=1); self.form_frame = ctk.CTkFrame(right_panel, fg_color="transparent"); self.form_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20); self.form_frame.grid_columnconfigure(0, weight=1); self.form_frame.grid_rowconfigure(1, weight=1); ctk.CTkLabel(self.form_frame, text=f"{self.item_name} Details", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 20)); self.fields_container = ctk.CTkFrame(self.form_frame, fg_color="transparent"); self.fields_container.grid(row=1, column=0, sticky="nsew"); self.create_form_fields()
    def create_form_fields(self):
        self.form_entries = {};
        for i, (key, label) in enumerate(self.fields.items()):
            ctk.CTkLabel(self.fields_container, text=label, width=120, anchor="w").grid(row=i, column=0, sticky="w", pady=5);
            if key == "notes": entry = ctk.CTkTextbox(self.fields_container, height=100)
            else: entry = ctk.CTkEntry(self.fields_container)
            entry.grid(row=i, column=1, sticky="ew", padx=(10, 0), pady=5); self.fields_container.grid_columnconfigure(1, weight=1); self.form_entries[key] = entry
        button_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent"); button_frame.grid(row=2, column=0, sticky="ew", pady=(20, 0)); button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1); self.save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_item); self.save_button.grid(row=0, column=0, padx=(0, 5), sticky="ew"); self.clear_button = ctk.CTkButton(button_frame, text="Clear / New", command=self.clear_form); self.clear_button.grid(row=0, column=1, padx=5, sticky="ew"); self.import_button = ctk.CTkButton(button_frame, text="Import CSV", command=self.import_csv); self.import_button.grid(row=0, column=2, padx=5, sticky="ew"); self.delete_button = ctk.CTkButton(button_frame, text="Delete", command=self.delete_item, state="disabled", fg_color="#D32F2F", hover_color="#B71C1C"); self.delete_button.grid(row=0, column=3, padx=(5, 0), sticky="ew")
    def select_item(self, item): self.clear_form(); self.selected_item_id = item['id']; [entry.insert("1.0", item.get(key) or "") if isinstance(entry, ctk.CTkTextbox) else entry.insert(0, str(item.get(key) or "")) for key, entry in self.form_entries.items()]; self.delete_button.configure(state="normal")
    def refresh_data(self): self.filter_list(); self.clear_form()
    def filter_list(self, event=None):
        items = self.db_search(self.search_entry.get()); [widget.destroy() for widget in self.item_list_frame.winfo_children()]; [ctk.CTkButton(self.item_list_frame, text=item['name'], anchor="w", fg_color="transparent", hover=False, command=lambda i=item: self.select_item(i)).pack(fill="x", padx=5, pady=2) for item in items]
    def clear_form(self): self.selected_item_id = None; [entry.delete("1.0", "end") if isinstance(entry, ctk.CTkTextbox) else entry.delete(0, "end") for entry in self.form_entries.values()]; self.delete_button.configure(state="disabled"); self.form_entries[list(self.fields.keys())[0]].focus()
    def save_item(self):
        values = [entry.get("1.0", "end-1c") if isinstance(entry, ctk.CTkTextbox) else entry.get() for entry in self.form_entries.values()];
        if not values[0]: messagebox.showerror("Error", f"{self.fields[list(self.fields.keys())[0]]} is required."); return
        if self.selected_item_id: self.db_update(self.selected_item_id, *values)
        else: self.db_add(*values)
        self.refresh_data(); messagebox.showinfo("Success", f"{self.item_name} saved successfully.")
    def delete_item(self):
        if self.selected_item_id and messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this {self.item_name}?"): self.db_delete(self.selected_item_id); self.refresh_data(); messagebox.showinfo("Success", f"{self.item_name} deleted.")
    def import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")]);
        if not file_path: return
        try: table_name = 'customers' if self.item_name == 'Customer' else 'products'; self.db.import_from_csv(file_path, table_name); self.refresh_data(); messagebox.showinfo("Success", f"{self.title} imported successfully.")
        except Exception as e: messagebox.showerror("Import Error", f"An error occurred: {e}")
class CustomersFrame(BaseCrudFrame):
    def __init__(self, master, app_instance, db): super().__init__(master, app_instance, db, title="Customers", item_name="Customer", fields={"name": "Name*", "email": "Email", "phone": "Phone", "address": "Address", "notes": "Notes"}, db_get_all=db.get_customers, db_add=db.add_customer, db_update=db.update_customer, db_delete=db.delete_customer, db_search=db.get_customers, db_import=lambda path: db.import_from_csv(path, 'customers'))
class InventoryFrame(BaseCrudFrame):
    def __init__(self, master, app_instance, db): super().__init__(master, app_instance, db, title="Inventory", item_name="Product", fields={"name": "Product Name*", "master_price": "Master Price*", "category": "Category"}, db_get_all=db.get_products, db_add=db.add_product, db_update=db.update_product, db_delete=db.delete_product, db_search=db.get_products, db_import=lambda path: db.import_from_csv(path, 'products'))
class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance, db):
        super().__init__(master, fg_color="transparent")
        self.app, self.db = app_instance, db

    def refresh_data(self):
        for widget in self.winfo_children(): widget.destroy()
        
        appearance_frame = ctk.CTkFrame(self); appearance_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(appearance_frame, text="Appearance", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=10)
        theme_menu = ctk.CTkOptionMenu(appearance_frame, values=["Light (Custom)", "Dark", "System"], command=self.change_theme)
        theme_menu.set(self.app.THEME_NAME); theme_menu.pack(pady=10, padx=10, anchor="w")
        
        smtp_frame = ctk.CTkFrame(self); smtp_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(smtp_frame, text="SMTP Email Settings (for future use)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=10)
        self.smtp_entries = {}
        for field in ["SMTP Host", "Port", "Username", "Password"]:
            frame = ctk.CTkFrame(smtp_frame, fg_color="transparent"); frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(frame, text=field, width=100, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(frame, show="*" if field == "Password" else None); key = f"smtp_{field.lower().replace(' ', '_')}"
            entry.insert(0, self.db.get_setting(key) or ""); entry.pack(side="left", expand=True, fill="x")
            self.smtp_entries[key] = entry
        ctk.CTkButton(smtp_frame, text="Save SMTP Settings", command=self.save_smtp_settings).pack(pady=20, padx=10, anchor="e")
    
    def change_theme(self, new_theme: str):
        self.db.set_setting("theme", new_theme)
        messagebox.showinfo("Theme Change", f"Theme set to '{new_theme}'. Please restart the application to apply changes.")
    
    def save_smtp_settings(self):
        for key, entry in self.smtp_entries.items(): self.db.set_setting(key, entry.get())
        messagebox.showinfo("Success", "SMTP settings saved.")
class VendorFulfillmentWindow(ctk.CTkToplevel):
    def __init__(self, master, db, order_id):
        super().__init__(master); self.db, self.order_id = db, order_id; self.title(f"Fulfill Order #{order_id}"); self.geometry("500x600"); self.transient(master); self.grab_set(); self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1); scroll_frame = ctk.CTkScrollableFrame(self, label_text="Order Items"); scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10); scroll_frame.grid_columnconfigure(0, weight=1); self.fulfillment_entries = {}
        for item in self.db.get_order_items(self.order_id):
            item_frame = ctk.CTkFrame(scroll_frame); item_frame.pack(fill="x", pady=5, padx=5); item_frame.grid_columnconfigure(1, weight=1); ctk.CTkLabel(item_frame, text=f"{item['name']} (Qty: {item['quantity']})", wraplength=200).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5); ctk.CTkLabel(item_frame, text="Final Price:").grid(row=1, column=0, sticky="w", padx=5); price_entry = ctk.CTkEntry(item_frame); price_entry.grid(row=1, column=1, sticky="ew", padx=5); out_of_stock_check = ctk.CTkCheckBox(item_frame, text="Out of Stock"); out_of_stock_check.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5); self.fulfillment_entries[item['id']] = {"price_entry": price_entry, "out_of_stock_check": out_of_stock_check}
        ctk.CTkButton(self, text="Submit Fulfillment", command=self.submit).grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    def submit(self):
        fulfillment_data = {};
        for item_id, widgets in self.fulfillment_entries.items():
            price, out_of_stock = widgets['price_entry'].get(), bool(widgets['out_of_stock_check'].get())
            if not out_of_stock:
                if not price: messagebox.showerror("Input Error", "Price is required for in-stock items."); return
                try: float(price)
                except ValueError: messagebox.showerror("Input Error", f"Invalid price: '{price}'."); return
            fulfillment_data[item_id] = {"price": price, "out_of_stock": out_of_stock}
        self.db.update_order_fulfillment(fulfillment_data); messagebox.showinfo("Success", f"Order #{self.order_id} fulfilled."); self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
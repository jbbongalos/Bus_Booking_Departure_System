import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3

conn = sqlite3.connect("bus_system.db")
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS buses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT,
        capacity INTEGER,
        departure TEXT,
        destination TEXT,
        departure_time TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS passengers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        bus_id INTEGER,
        FOREIGN KEY(bus_id) REFERENCES buses(id)
    )
""")

conn.commit()

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self, bg="#e6f2ff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

root = tk.Tk()
root.title("Bus Booking & Departure System")
root.geometry("1000x700")
root.configure(bg="#e6f2ff")

style = ttk.Style()
style.theme_use("default")
style.configure("TButton", font=("Segoe UI", 11), padding=6)
style.configure("TLabel", font=("Segoe UI", 11), background="#e6f2ff")
style.configure("TEntry", font=("Segoe UI", 11))
style.configure("TCombobox", font=("Segoe UI", 11))

scrollable = ScrollableFrame(root)
scrollable.pack(fill="both", expand=True)
main_frame = scrollable.scrollable_frame

current_admin = None

def show_frame(frame):
    for widget in main_frame.winfo_children():
        widget.pack_forget()
    frame.pack(fill="both", expand=True)

def register_admin():
    username = reg_username.get()
    password = reg_password.get()
    if username and password:
        try:
            c.execute("INSERT INTO admins VALUES (?, ?)", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "Admin registered.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")
    else:
        messagebox.showwarning("Input", "Please fill all fields.")

def login_admin():
    global current_admin
    username = login_username.get()
    password = login_password.get()
    c.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
    if c.fetchone():
        current_admin = username
        show_frame(admin_menu)
        update_bus_comboboxes()
        view_buses()
        view_passengers()
    else:
        messagebox.showerror("Error", "Invalid credentials.")

def add_bus():
    name = bus_name.get()
    btype = bus_type.get()
    dep = bus_departure.get()
    dest = bus_destination.get()
    dep_time = bus_departure_time.get()
    try:
        capacity = int(bus_capacity.get())
        c.execute("INSERT INTO buses (name, type, capacity, departure, destination, departure_time) VALUES (?, ?, ?, ?, ?, ?)",
                  (name, btype, capacity, dep, dest, dep_time))
        conn.commit()
        messagebox.showinfo("Success", "Bus added.")
        view_buses()
        update_bus_comboboxes()
    except ValueError:
        messagebox.showerror("Error", "Capacity must be a number.")

def view_buses():
    for row in bus_tree.get_children():
        bus_tree.delete(row)
    for row in c.execute("SELECT * FROM buses"):
        bus_tree.insert("", "end", values=row)

def view_passengers():
    for row in passenger_tree.get_children():
        passenger_tree.delete(row)
    for row in c.execute("SELECT p.id, p.name, b.name FROM passengers p JOIN buses b ON p.bus_id = b.id"):
        passenger_tree.insert("", "end", values=row)

def register_passenger():
    name = passenger_name.get()
    bus = selected_bus.get()
    if name and bus:
        c.execute("SELECT id, capacity FROM buses WHERE name=?", (bus,))
        result = c.fetchone()
        if not result:
            messagebox.showerror("Error", "Bus not found.")
            return
        bus_id, capacity = result
        c.execute("SELECT COUNT(*) FROM passengers WHERE bus_id=?", (bus_id,))
        count = c.fetchone()[0]
        c.execute("SELECT * FROM passengers WHERE name=? AND bus_id=?", (name, bus_id))
        if c.fetchone():
            messagebox.showerror("Error", "Passenger already booked on this bus.")
        elif count >= capacity:
            messagebox.showwarning("Full", "Bus is already full.")
        else:
            c.execute("INSERT INTO passengers (name, bus_id) VALUES (?, ?)", (name, bus_id))
            conn.commit()
            messagebox.showinfo("Success", "Passenger registered.")
            view_passengers()

def update_bus_comboboxes():
    c.execute("SELECT name FROM buses")
    bus_names = [b[0] for b in c.fetchall()]
    selected_bus_cb['values'] = bus_names
    view_buses()  

def edit_selected_bus():
    selected = bus_tree.selection()
    if not selected:
        messagebox.showwarning("Select", "Please select a bus to edit.")
        return
    bus_data = bus_tree.item(selected[0], "values")
    bus_id = bus_data[0]

    edit_win = tk.Toplevel(root)
    edit_win.title("Edit Bus")

    fields = ["Name", "Type", "Capacity", "Departure", "Destination", "Departure Time"]
    entries = {}

    for i, field in enumerate(fields):
        ttk.Label(edit_win, text=field).grid(row=i, column=0, pady=2, padx=5)
        ent = ttk.Entry(edit_win)
        ent.grid(row=i, column=1, pady=2, padx=5)
        ent.insert(0, bus_data[i+1])
        entries[field] = ent

    def save_changes():
        try:
            name = entries["Name"].get()
            btype = entries["Type"].get()
            capacity = int(entries["Capacity"].get())
            dep = entries["Departure"].get()
            dest = entries["Destination"].get()
            dep_time = entries["Departure Time"].get()
            c.execute("""UPDATE buses SET name=?, type=?, capacity=?, departure=?, destination=?, departure_time=? WHERE id=?""",
                      (name, btype, capacity, dep, dest, dep_time, bus_id))
            conn.commit()
            messagebox.showinfo("Success", "Bus updated.")
            edit_win.destroy()
            view_buses()
            update_bus_comboboxes()
        except ValueError:
            messagebox.showerror("Error", "Capacity must be a number.")

    ttk.Button(edit_win, text="Save", command=save_changes).grid(row=len(fields), column=0, columnspan=2, pady=10)

def delete_selected_bus():
    selected = bus_tree.selection()
    if not selected:
        messagebox.showwarning("Select", "Please select a bus to delete.")
        return
    bus_data = bus_tree.item(selected[0], "values")
    bus_id = bus_data[0]

    
    c.execute("SELECT COUNT(*) FROM passengers WHERE bus_id=?", (bus_id,))
    count = c.fetchone()[0]
    if count > 0:
        messagebox.showerror("Error", "Cannot delete bus with registered passengers.")
        return

    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this bus?"):
        c.execute("DELETE FROM buses WHERE id=?", (bus_id,))
        conn.commit()
        messagebox.showinfo("Deleted", "Bus deleted.")
        view_buses()
        update_bus_comboboxes()

def edit_selected_passenger():
    selected = passenger_tree.selection()
    if not selected:
        messagebox.showwarning("Select", "Please select a passenger to edit.")
        return
    passenger_data = passenger_tree.item(selected[0], "values")
    passenger_id = passenger_data[0]

    
    edit_win = tk.Toplevel(root)
    edit_win.title("Edit Passenger")

    ttk.Label(edit_win, text="Name").grid(row=0, column=0, pady=2, padx=5)
    name_entry = ttk.Entry(edit_win)
    name_entry.grid(row=0, column=1, pady=2, padx=5)
    name_entry.insert(0, passenger_data[1])

    ttk.Label(edit_win, text="Bus").grid(row=1, column=0, pady=2, padx=5)
    
    c.execute("SELECT name FROM buses")
    bus_names = [b[0] for b in c.fetchall()]
    bus_cb = ttk.Combobox(edit_win, values=bus_names)
    bus_cb.grid(row=1, column=1, pady=2, padx=5)
    bus_cb.set(passenger_data[2])

    def save_changes():
        new_name = name_entry.get()
        new_bus_name = bus_cb.get()
        if not new_name or not new_bus_name:
            messagebox.showerror("Error", "All fields are required.")
            return
        
        c.execute("SELECT id, capacity FROM buses WHERE name=?", (new_bus_name,))
        result = c.fetchone()
        if not result:
            messagebox.showerror("Error", "Selected bus not found.")
            return
        bus_id, capacity = result
        
        c.execute("SELECT COUNT(*) FROM passengers WHERE bus_id=?", (bus_id,))
        count = c.fetchone()[0]
        
        c.execute("SELECT * FROM passengers WHERE name=? AND bus_id=? AND id!=?", (new_name, bus_id, passenger_id))
        if c.fetchone():
            messagebox.showerror("Error", "Passenger already booked on this bus.")
            return
        if count >= capacity:
            messagebox.showwarning("Full", "Selected bus is full.")
            return

        c.execute("UPDATE passengers SET name=?, bus_id=? WHERE id=?", (new_name, bus_id, passenger_id))
        conn.commit()
        messagebox.showinfo("Success", "Passenger updated.")
        edit_win.destroy()
        view_passengers()

    ttk.Button(edit_win, text="Save", command=save_changes).grid(row=2, column=0, columnspan=2, pady=10)

def generate_receipt():
    selected = passenger_tree.selection()
    if not selected:
        messagebox.showwarning("Select", "Please select a passenger to generate receipt.")
        return
    passenger_data = passenger_tree.item(selected[0], "values")
    passenger_id, passenger_name_val, bus_name_val = passenger_data

    c.execute("SELECT departure, destination, departure_time, capacity FROM buses WHERE name=?", (bus_name_val,))
    bus_info = c.fetchone()
    if not bus_info:
        messagebox.showerror("Error", "Bus details not found.")
        return
    departure, destination, departure_time, capacity = bus_info

    receipt_text = (
        f"--- Bus Booking Receipt ---\n\n"
        f"Passenger Name: {passenger_name_val}\n"
        f"Bus Name: {bus_name_val}\n"
        f"Departure: {departure}\n"
        f"Destination: {destination}\n"
        f"Departure Time: {departure_time}\n"
        f"Capacity: {capacity}\n\n"
        f"Thank you for booking with us!"
    )

    receipt_win = tk.Toplevel(root)
    receipt_win.title("Booking Receipt")
    receipt_win.geometry("350x250")
    ttk.Label(receipt_win, text=receipt_text, justify="left").pack(padx=10, pady=10)

def delete_selected_passenger():
    selected = passenger_tree.selection()
    if not selected:
        messagebox.showwarning("Select", "Please select a passenger to delete.")
        return
    passenger_data = passenger_tree.item(selected[0], "values")
    passenger_id = passenger_data[0]

    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this passenger?"):
        c.execute("DELETE FROM passengers WHERE id=?", (passenger_id,))
        conn.commit()
        messagebox.showinfo("Deleted", "Passenger deleted.")
        view_passengers()

login_frame = ttk.Frame(main_frame)
register_frame = ttk.Frame(main_frame)
admin_menu = ttk.Frame(main_frame)

ttk.Label(login_frame, text="Admin Login", font=("Segoe UI", 16, "bold")).pack(pady=10)
login_username = tk.StringVar()
login_password = tk.StringVar()
ttk.Label(login_frame, text="Username").pack(pady=2)
ttk.Entry(login_frame, textvariable=login_username).pack(pady=2)
ttk.Label(login_frame, text="Password").pack(pady=2)
ttk.Entry(login_frame, textvariable=login_password, show='*').pack(pady=2)
ttk.Button(login_frame, text="Login", command=login_admin).pack(pady=5)
ttk.Button(login_frame, text="Register", command=lambda: show_frame(register_frame)).pack(pady=2)

ttk.Label(register_frame, text="Admin Registration", font=("Segoe UI", 16, "bold")).pack(pady=10)
reg_username = tk.StringVar()
reg_password = tk.StringVar()
ttk.Label(register_frame, text="Username").pack(pady=2)
ttk.Entry(register_frame, textvariable=reg_username).pack(pady=2)
ttk.Label(register_frame, text="Password").pack(pady=2)
ttk.Entry(register_frame, textvariable=reg_password, show='*').pack(pady=2)
ttk.Button(register_frame, text="Register", command=register_admin).pack(pady=5)
ttk.Button(register_frame, text="Back to Login", command=lambda: show_frame(login_frame)).pack(pady=2)

bus_name = tk.StringVar()
bus_type = tk.StringVar()
bus_capacity = tk.StringVar()
bus_departure = tk.StringVar()
bus_destination = tk.StringVar()
bus_departure_time = tk.StringVar()

passenger_name = tk.StringVar()
selected_bus = tk.StringVar()

selected_bus_cb = ttk.Combobox(admin_menu, textvariable=selected_bus)

ttk.Label(admin_menu, text="Bus Information", font=("Segoe UI", 14, "bold")).pack(pady=10)

ttk.Label(admin_menu, text="Bus Name").pack()
bus_name_cb = ttk.Combobox(admin_menu, textvariable=bus_name)
bus_name_cb['values'] = ["Raymond", "Express", "CityLink", "InterCity", "MountainView"]  # Example bus names
bus_name_cb.pack(pady=2)

ttk.Label(admin_menu, text="Bus Type").pack()
bus_type_cb = ttk.Combobox(admin_menu, textvariable=bus_type)
bus_type_cb['values'] = ["AC", "Ordinary"]
bus_type_cb.pack(pady=2)

ttk.Label(admin_menu, text="Capacity").pack()
ttk.Entry(admin_menu, textvariable=bus_capacity).pack(pady=2)

ttk.Label(admin_menu, text="Place of Departure").pack()
ttk.Entry(admin_menu, textvariable=bus_departure).pack(pady=2)

ttk.Label(admin_menu, text="Place of Destination").pack()
ttk.Entry(admin_menu, textvariable=bus_destination).pack(pady=2)

ttk.Label(admin_menu, text="Time of Departure").pack()
ttk.Entry(admin_menu, textvariable=bus_departure_time).pack(pady=2)

ttk.Button(admin_menu, text="Add Bus", command=add_bus).pack(pady=5)

bus_tree = ttk.Treeview(admin_menu, columns=("ID", "Name", "Type", "Capacity", "Departure", "Destination", "Departure Time"), show='headings')

for col in ("ID", "Name", "Type", "Capacity", "Departure", "Destination", "Departure Time"):
    bus_tree.heading(col, text=col)
    if col == "ID":
        bus_tree.column(col, width=40, anchor="center")
    elif col == "Capacity":
        bus_tree.column(col, width=80, anchor="center")
    else:
        bus_tree.column(col, width=130, anchor="w")

bus_tree.pack(pady=10, fill='x')

bus_scrollbar = ttk.Scrollbar(admin_menu, orient="vertical", command=bus_tree.yview)
bus_tree.configure(yscrollcommand=bus_scrollbar.set)
bus_scrollbar.pack(side="right", fill="y")

bus_buttons_frame = ttk.Frame(admin_menu)
bus_buttons_frame.pack(pady=5)

ttk.Button(bus_buttons_frame, text="Edit Selected Bus", command=edit_selected_bus).pack(side="left", padx=5)
ttk.Button(bus_buttons_frame, text="Delete Selected Bus", command=delete_selected_bus).pack(side="left", padx=5)
ttk.Button(bus_buttons_frame, text="Refresh Bus List", command=view_buses).pack(side="left", padx=5)

ttk.Label(admin_menu, text="Passenger Registration", font=("Segoe UI", 14, "bold")).pack(pady=10)

ttk.Label(admin_menu, text="Passenger Name").pack()
ttk.Entry(admin_menu, textvariable=passenger_name).pack(pady=2)

ttk.Label(admin_menu, text="Select Bus").pack()
selected_bus_cb.pack(pady=2)

ttk.Button(admin_menu, text="Register Passenger", command=register_passenger).pack(pady=5)

ttk.Label(admin_menu, text="Registered Passengers", font=("Segoe UI", 14, "bold")).pack(pady=10)

passenger_tree = ttk.Treeview(admin_menu, columns=("ID", "Name", "Bus"), show='headings')
for col in ("ID", "Name", "Bus"):
    passenger_tree.heading(col, text=col)
    passenger_tree.column(col, width=150, anchor="w")

passenger_tree.pack(pady=10, fill='x')

passenger_buttons_frame = ttk.Frame(admin_menu)
passenger_buttons_frame.pack(pady=5)

ttk.Button(passenger_buttons_frame, text="Edit Selected Passenger", command=edit_selected_passenger).pack(side="left", padx=5)
ttk.Button(passenger_buttons_frame, text="Delete Selected Passenger", command=delete_selected_passenger).pack(side="left", padx=5)
ttk.Button(passenger_buttons_frame, text="Refresh Passenger List", command=view_passengers).pack(side="left", padx=5)
ttk.Button(passenger_buttons_frame, text="Generate Receipt", command=generate_receipt).pack(side="left", padx=5)

show_frame(login_frame)
root.mainloop()
tk.tk
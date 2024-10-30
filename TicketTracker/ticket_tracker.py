import csv
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import time
import os
import json
import uuid
from datetime import datetime

CSV_FILE_PATH = r'D:\OBS\OBSAutomation\tickets.csv'
COMPLETED_CSV_FILE = 'D:\OBS\OBSAutomation\completed_tickets.csv'
IN_PROGRESS_CSV_FILE = 'D:\OBS\OBSAutomation\in_progress_tickets.csv'
COMMENTS_FILE = 'comments.json'
TICKET_ID_FILE = 'ticket_ids.json'

class TicketTracker:
    def __init__(self, master):
        self.master = master
        master.title("Ticket Tracker")

        self.open_tickets = []
        self.in_progress_tickets = []
        self.complete_tickets = []
        self.comments = self.load_comments()
        self.ticket_ids = self.load_ticket_ids()

        self.processing_move = False  # Flag to prevent re-entrant calls
        self.create_widgets()
        self.load_tickets()
        self.start_auto_refresh()

        # Bind the spacebar key to move tickets
        self.master.bind('<Key>', self.on_spacebar_press)

    def create_widgets(self):
        # Set dark mode colors
        self.bg_color = "#2E2E2E"            # Dark background
        self.fg_color = "#FFFFFF"            # White foreground
        self.highlight_color = "#FFD700"     # Gold color for highlighting
        self.button_color = "#4E4E4E"
        self.open_ticket_bg = "#3B3B3B"
        self.in_progress_ticket_bg = "#424242"
        self.complete_ticket_bg = "#2A2A2A"
        self.high_priority_color = "#8B0000"  # Dark Red for high priority tickets

        self.master.configure(bg=self.bg_color)

        # Main frames for Open, In Progress, and Complete tickets
        self.open_frame = tk.LabelFrame(self.master, text="Open", padx=10, pady=10, bg=self.bg_color, fg=self.fg_color)
        self.open_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.in_progress_frame = tk.LabelFrame(self.master, text="In Progress", padx=10, pady=10, bg=self.bg_color, fg=self.fg_color)
        self.in_progress_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.complete_frame = tk.LabelFrame(self.master, text="Complete", padx=10, pady=10, bg=self.bg_color, fg=self.fg_color)
        self.complete_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollable canvas for Open tickets
        self.open_canvas = tk.Canvas(self.open_frame, bg=self.bg_color, highlightthickness=0)
        self.open_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.open_scrollbar = ttk.Scrollbar(self.open_frame, orient="vertical", command=self.open_canvas.yview)
        self.open_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.open_canvas.configure(yscrollcommand=self.open_scrollbar.set)
        # Bind the scroll region update to the container frame
        self.open_container = tk.Frame(self.open_canvas, bg=self.bg_color)
        self.open_canvas.create_window((0, 0), window=self.open_container, anchor="nw")
        self.open_container.bind('<Configure>', lambda e: self.open_canvas.configure(scrollregion=self.open_canvas.bbox("all")))
        # Bind mouse wheel scrolling
        self.open_canvas.bind('<Enter>', lambda e: self.bind_mousewheel(self.open_canvas))
        self.open_canvas.bind('<Leave>', lambda e: self.unbind_mousewheel(self.open_canvas))

        # Scrollable canvas for In Progress tickets
        self.in_progress_canvas = tk.Canvas(self.in_progress_frame, bg=self.bg_color, highlightthickness=0)
        self.in_progress_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.in_progress_scrollbar = ttk.Scrollbar(self.in_progress_frame, orient="vertical", command=self.in_progress_canvas.yview)
        self.in_progress_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.in_progress_canvas.configure(yscrollcommand=self.in_progress_scrollbar.set)
        self.in_progress_container = tk.Frame(self.in_progress_canvas, bg=self.bg_color)
        self.in_progress_canvas.create_window((0, 0), window=self.in_progress_container, anchor="nw")
        self.in_progress_container.bind('<Configure>', lambda e: self.in_progress_canvas.configure(scrollregion=self.in_progress_canvas.bbox("all")))
        self.in_progress_canvas.bind('<Enter>', lambda e: self.bind_mousewheel(self.in_progress_canvas))
        self.in_progress_canvas.bind('<Leave>', lambda e: self.unbind_mousewheel(self.in_progress_canvas))

        # Scrollable canvas for Complete tickets
        self.complete_canvas = tk.Canvas(self.complete_frame, bg=self.bg_color, highlightthickness=0)
        self.complete_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.complete_scrollbar = ttk.Scrollbar(self.complete_frame, orient="vertical", command=self.complete_canvas.yview)
        self.complete_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.complete_canvas.configure(yscrollcommand=self.complete_scrollbar.set)
        self.complete_container = tk.Frame(self.complete_canvas, bg=self.bg_color)
        self.complete_canvas.create_window((0, 0), window=self.complete_container, anchor="nw")
        self.complete_container.bind('<Configure>', lambda e: self.complete_canvas.configure(scrollregion=self.complete_canvas.bbox("all")))
        self.complete_canvas.bind('<Enter>', lambda e: self.bind_mousewheel(self.complete_canvas))
        self.complete_canvas.bind('<Leave>', lambda e: self.unbind_mousewheel(self.complete_canvas))

        # Buttons to move tickets
        self.move_to_in_progress_button = tk.Button(self.master, text="Move to In Progress >>", command=self.move_to_in_progress_button_click, font=("Arial", 12, "bold"),
                                         bg=self.button_color, fg=self.fg_color, activebackground=self.highlight_color)
        self.move_to_in_progress_button.pack(pady=5)

        self.move_to_complete_button = tk.Button(self.master, text="Move to Complete >>", command=self.move_to_complete_button_click, font=("Arial", 12, "bold"),
                                         bg=self.button_color, fg=self.fg_color, activebackground=self.highlight_color)
        self.move_to_complete_button.pack(pady=5)

        # Delete button
        self.delete_button = tk.Button(self.master, text="Delete Ticket", command=self.delete_ticket, font=("Arial", 12, "bold"),
                                           fg="red", bg=self.button_color, activebackground=self.highlight_color)
        self.delete_button.pack(pady=5)

    # Methods to bind and unbind mouse wheel events
    def bind_mousewheel(self, canvas):
        if os.name == 'nt':  # Windows
            canvas.bind_all('<MouseWheel>', lambda event: self.on_mousewheel(event, canvas))
        elif os.name == 'posix':  # macOS or Linux
            canvas.bind_all('<Button-4>', lambda event: self.on_mousewheel(event, canvas))
            canvas.bind_all('<Button-5>', lambda event: self.on_mousewheel(event, canvas))

    def unbind_mousewheel(self, canvas):
        if os.name == 'nt':
            canvas.unbind_all('<MouseWheel>')
        elif os.name == 'posix':
            canvas.unbind_all('<Button-4>')
            canvas.unbind_all('<Button-5>')

    def on_mousewheel(self, event, canvas):
        if os.name == 'nt':
            canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
        elif os.name == 'posix':
            if event.num == 4:
                canvas.yview_scroll(-1, 'units')
            elif event.num == 5:
                canvas.yview_scroll(1, 'units')

    # New method to handle spacebar press
    def on_spacebar_press(self, event):
        if event.keysym == 'space':
            if not self.processing_move and hasattr(self, 'selected_ticket') and self.selected_ticket is not None:
                ticket_data = self.selected_ticket
                self.selected_ticket = None  # Clear selected_ticket immediately
                self.processing_move = True  # Set the flag to prevent re-entry
                try:
                    # Check if the selected ticket is in Open tickets
                    if any(ticket_data == t[0] for t in self.open_tickets):
                        self.move_to_in_progress(ticket_data)
                    # Else if it's in In Progress tickets
                    elif any(ticket_data == t[0] for t in self.in_progress_tickets):
                        self.move_to_complete(ticket_data)
                    else:
                        # Ticket is not in expected list
                        pass
                finally:
                    self.processing_move = False

    def load_comments(self):
        if os.path.exists(COMMENTS_FILE):
            with open(COMMENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}

    def save_comments(self):
        with open(COMMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.comments, f, ensure_ascii=False, indent=4)

    def load_ticket_ids(self):
        if os.path.exists(TICKET_ID_FILE):
            with open(TICKET_ID_FILE, 'r', encoding='utf-8') as f:
                self.ticket_ids = json.load(f)
        else:
            self.ticket_ids = {}
        # Initialize next_ticket_id
        self.next_ticket_id = 1
        for tid in self.ticket_ids.values():
            try:
                numeric_id = int(tid)
                if numeric_id >= self.next_ticket_id:
                    self.next_ticket_id = numeric_id +1
            except ValueError:
                pass  # Ignore non-integer IDs
        return self.ticket_ids

    def save_ticket_ids(self):
        with open(TICKET_ID_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.ticket_ids, f, ensure_ascii=False, indent=4)

    def parse_date(self, date_str):
        try:
            # Adjust the format string to match your 'Time Placed' format
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # If parsing fails, return a default date
            return datetime.min

    def load_tickets(self):
        # Reset selected_ticket
        self.selected_ticket = None

        # Clear current tickets
        for widget in self.open_container.winfo_children():
            widget.destroy()
        for widget in self.in_progress_container.winfo_children():
            widget.destroy()
        for widget in self.complete_container.winfo_children():
            widget.destroy()
        self.open_tickets.clear()
        self.in_progress_tickets.clear()
        self.complete_tickets.clear()

        # Read completed tickets
        completed_tickets_dict = self.read_completed_tickets()
        # Read in-progress tickets
        in_progress_tickets_dict = self.read_in_progress_tickets()

        # Read tickets from CSV
        tickets_list = []
        try:
            with open(CSV_FILE_PATH, newline='', encoding='utf-8') as csvfile:
                ticket_reader = csv.DictReader(csvfile)
                for row in ticket_reader:
                    # Skip tickets where any field is 'DefaulT' or empty
                    if self.is_invalid_ticket(row):
                        continue  # Skip this row

                    ticket_id = self.get_or_create_ticket_id(row)
                    ticket_info = f"ID: {ticket_id}\n{row['Username']} - ({row['Time Placed']})"

                    if ticket_id not in completed_tickets_dict and ticket_id not in in_progress_tickets_dict:
                        tickets_list.append((row, ticket_info, ticket_id))
        except FileNotFoundError:
            print(f"Error: CSV file not found at {CSV_FILE_PATH}")
            return

        # Sort tickets by priority and date
        def priority_value(priority):
            return 0 if priority.strip().lower() == 'high' else 1  # High priority gets 0, Low gets 1

        tickets_list.sort(key=lambda x: (priority_value(x[0].get('Priority', 'Low')), self.parse_date(x[0]['Time Placed'])))

        # Add tickets to Open tickets display
        for row, ticket_info, ticket_id in tickets_list:
            self.open_tickets.append((row, ticket_info, ticket_id))
            self.add_ticket_to_open(row, ticket_info, ticket_id)

        # Read and sort in-progress tickets
        in_progress_tickets_list = []
        for ticket_id, ticket in in_progress_tickets_dict.items():
            ticket_data = ticket['ticket_data']
            ticket_info = f"ID: {ticket_id}\n{ticket_data['Username']} - ({ticket_data['Time Placed']})"
            in_progress_tickets_list.append((ticket_data, ticket_info, ticket_id))

        in_progress_tickets_list.sort(key=lambda x: (priority_value(x[0].get('Priority', 'Low')), self.parse_date(x[0]['Time Placed'])))

        # Add in-progress tickets to In Progress tickets display
        for ticket_data, ticket_info, ticket_id in in_progress_tickets_list:
            self.in_progress_tickets.append((ticket_data, ticket_info, ticket_id))
            self.add_ticket_to_in_progress(ticket_data, ticket_info, ticket_id)

        # Read and sort completed tickets
        completed_tickets_list = []
        for ticket_id, ticket in completed_tickets_dict.items():
            ticket_data = ticket['ticket_data']
            ticket_info = f"ID: {ticket_id}\n{ticket_data['Username']} - ({ticket_data['Time Placed']})"
            completed_tickets_list.append((ticket_data, ticket_info, ticket_id))

        # Sort completed tickets by priority and date
        completed_tickets_list.sort(key=lambda x: (priority_value(x[0].get('Priority', 'Low')), self.parse_date(x[0]['Time Placed'])))

        # Add completed tickets to the Complete tickets display
        for ticket_data, ticket_info, ticket_id in completed_tickets_list:
            self.complete_tickets.append((ticket_data, ticket_info, ticket_id))
            self.add_ticket_to_complete(ticket_data, ticket_info, ticket_id)

        # Schedule the next refresh
        self.master.after(30000, self.load_tickets)

    def is_invalid_ticket(self, row):
        for value in row.values():
            if not value.strip() or value.strip().lower() == 'default':
                return True
        return False

    def get_or_create_ticket_id(self, ticket_data):
        ticket_key = self.generate_ticket_key(ticket_data)
        if ticket_key in self.ticket_ids:
            return self.ticket_ids[ticket_key]
        else:
            new_id = f"{self.next_ticket_id:05d}"  # Format with leading zeros
            self.ticket_ids[ticket_key] = new_id
            self.next_ticket_id +=1  # Increment for next ticket
            self.save_ticket_ids()
            return new_id

    def generate_ticket_key(self, ticket):
        # Include Priority in the ticket key to maintain priority in data
        return f"{ticket['Username'].strip().lower()}_{ticket['Issue'].strip().lower()}_{ticket['Time Placed'].strip()}_{ticket['Priority'].strip().lower()}"

    def add_ticket_to_open(self, ticket_data, ticket_info, ticket_id):
        priority = ticket_data.get('Priority', 'Low').strip().lower()
        bg_color = self.high_priority_color if priority == 'high' else self.open_ticket_bg

        ticket_frame = tk.Frame(self.open_container, bg=bg_color, bd=2, relief="raised", padx=10, pady=10)
        ticket_frame.pack(fill=tk.X, pady=5)
        ticket_frame.ticket_data = ticket_data  # Store ticket data in frame

        # Issue summary (collapsible)
        issue_summary = ticket_data['Issue'][:50] + ('...' if len(ticket_data['Issue']) > 50 else '')
        issue_full = ticket_data['Issue']

        # Ticket Label with word wrap and collapsible issue
        ticket_label_text = f"{ticket_info}\nPriority: {ticket_data.get('Priority', 'Low')}\nIssue: {issue_summary}"
        ticket_label = tk.Label(ticket_frame, text=ticket_label_text, bg=bg_color, fg=self.fg_color,
                                font=("Arial", 12), justify="left", anchor="w", wraplength=600)
        ticket_label.pack(fill=tk.X)

        # Update wraplength dynamically
        def update_wraplength(event=None):
            try:
                new_wraplength = ticket_frame.winfo_width() - 20  # Subtract some padding
                if new_wraplength > 0:
                    ticket_label.config(wraplength=new_wraplength)
            except tk.TclError:
                # Widget has been destroyed; ignore the exception
                pass
        ticket_frame.bind('<Configure>', update_wraplength)
        update_wraplength()

        # Expand/Collapse function
        def toggle_issue(event=None):
            if ticket_label.cget('text') == ticket_label_text:
                ticket_label.config(text=f"{ticket_info}\nPriority: {ticket_data.get('Priority', 'Low')}\nIssue: {issue_full}")
            else:
                ticket_label.config(text=ticket_label_text)
            # Also select the ticket
            self.select_ticket(ticket_data)
            # Update wraplength
            update_wraplength()
            # Update scrollregion
            self.open_canvas.configure(scrollregion=self.open_canvas.bbox("all"))
            return "break"  # Prevent further propagation

        ticket_label.bind("<Button-1>", toggle_issue)

        # Buttons for comments and delete
        btn_frame = tk.Frame(ticket_frame, bg=bg_color)
        btn_frame.pack(fill=tk.X, pady=5)

        comment_button = tk.Button(btn_frame, text="Comments", command=lambda t=ticket_data: self.show_comments(t),
                                   bg=self.button_color, fg=self.fg_color, activebackground=self.highlight_color)
        comment_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(btn_frame, text="Delete", fg="red", command=lambda t=ticket_data: self.delete_ticket_from_open(t),
                                  bg=self.button_color, activebackground=self.highlight_color)
        delete_button.pack(side=tk.RIGHT, padx=5)

        # Bind click event to select ticket
        def select_ticket_event(event):
            self.select_ticket(ticket_data)
            return "break"  # Stop event propagation

        # Bind to ticket_frame and all widgets except ticket_label
        ticket_frame.bind("<Button-1>", select_ticket_event)
        for widget in ticket_frame.winfo_children():
            if widget != ticket_label:
                widget.bind("<Button-1>", select_ticket_event)

    def add_ticket_to_in_progress(self, ticket_data, ticket_info, ticket_id):
        priority = ticket_data.get('Priority', 'Low').strip().lower()
        bg_color = self.high_priority_color if priority == 'high' else self.in_progress_ticket_bg

        ticket_frame = tk.Frame(self.in_progress_container, bg=bg_color, bd=2, relief="raised", padx=10, pady=10)
        ticket_frame.pack(fill=tk.X, pady=5)
        ticket_frame.ticket_data = ticket_data  # Store ticket data in frame

        # Issue summary (collapsible)
        issue_summary = ticket_data['Issue'][:50] + ('...' if len(ticket_data['Issue']) > 50 else '')
        issue_full = ticket_data['Issue']

        # Ticket Label with word wrap and collapsible issue
        ticket_label_text = f"{ticket_info}\nPriority: {ticket_data.get('Priority', 'Low')}\nIssue: {issue_summary}"
        ticket_label = tk.Label(ticket_frame, text=ticket_label_text, bg=bg_color, fg=self.fg_color,
                                font=("Arial", 12), justify="left", anchor="w", wraplength=600)
        ticket_label.pack(fill=tk.X)

        # Update wraplength dynamically
        def update_wraplength(event=None):
            try:
                new_wraplength = ticket_frame.winfo_width() - 20
                if new_wraplength > 0:
                    ticket_label.config(wraplength=new_wraplength)
            except tk.TclError:
                pass
        ticket_frame.bind('<Configure>', update_wraplength)
        update_wraplength()

        # Expand/Collapse function
        def toggle_issue(event=None):
            if ticket_label.cget('text') == ticket_label_text:
                ticket_label.config(text=f"{ticket_info}\nPriority: {ticket_data.get('Priority', 'Low')}\nIssue: {issue_full}")
            else:
                ticket_label.config(text=ticket_label_text)
            # Also select the ticket
            self.select_ticket(ticket_data)
            # Update wraplength
            update_wraplength()
            # Update scrollregion
            self.in_progress_canvas.configure(scrollregion=self.in_progress_canvas.bbox("all"))
            return "break"  # Prevent further propagation

        ticket_label.bind("<Button-1>", toggle_issue)

        # Buttons for comments and delete
        btn_frame = tk.Frame(ticket_frame, bg=bg_color)
        btn_frame.pack(fill=tk.X, pady=5)

        comment_button = tk.Button(btn_frame, text="Comments", command=lambda t=ticket_data: self.show_comments(t),
                                   bg=self.button_color, fg=self.fg_color, activebackground=self.highlight_color)
        comment_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(btn_frame, text="Delete", fg="red", command=lambda t=ticket_data: self.delete_ticket_from_in_progress(t),
                                  bg=self.button_color, activebackground=self.highlight_color)
        delete_button.pack(side=tk.RIGHT, padx=5)

        # Bind click event to select ticket
        def select_ticket_event(event):
            self.select_ticket(ticket_data)
            return "break"  # Stop event propagation

        # Bind to ticket_frame and all widgets except ticket_label
        ticket_frame.bind("<Button-1>", select_ticket_event)
        for widget in ticket_frame.winfo_children():
            if widget != ticket_label:
                widget.bind("<Button-1>", select_ticket_event)

    def add_ticket_to_complete(self, ticket_data, ticket_info, ticket_id):
        priority = ticket_data.get('Priority', 'Low').strip().lower()
        bg_color = self.high_priority_color if priority == 'high' else self.complete_ticket_bg

        ticket_frame = tk.Frame(self.complete_container, bg=bg_color, bd=2, relief="raised", padx=10, pady=10)
        ticket_frame.pack(fill=tk.X, pady=5)
        ticket_frame.ticket_data = ticket_data  # Store ticket data in frame

        # Issue summary (collapsible)
        issue_summary = ticket_data['Issue'][:50] + ('...' if len(ticket_data['Issue']) > 50 else '')
        issue_full = ticket_data['Issue']

        # Ticket Label with word wrap and collapsible issue
        ticket_label_text = f"{ticket_info}\nPriority: {ticket_data.get('Priority', 'Low')}\nIssue: {issue_summary}"
        ticket_label = tk.Label(ticket_frame, text=ticket_label_text, bg=bg_color,
                                fg=self.fg_color, font=("Arial", 12), justify="left", anchor="w", wraplength=600)
        ticket_label.pack(fill=tk.X)

        # Update wraplength dynamically
        def update_wraplength(event=None):
            try:
                new_wraplength = ticket_frame.winfo_width() - 20
                if new_wraplength > 0:
                    ticket_label.config(wraplength=new_wraplength)
            except tk.TclError:
                pass
        ticket_frame.bind('<Configure>', update_wraplength)
        update_wraplength()

        # Expand/Collapse function
        def toggle_issue(event=None):
            if ticket_label.cget('text') == ticket_label_text:
                ticket_label.config(text=f"{ticket_info}\nPriority: {ticket_data.get('Priority', 'Low')}\nIssue: {issue_full}")
            else:
                ticket_label.config(text=ticket_label_text)
            # Also select the ticket
            self.select_ticket(ticket_data)
            # Update wraplength
            update_wraplength()
            # Update scrollregion
            self.complete_canvas.configure(scrollregion=self.complete_canvas.bbox("all"))
            return "break"  # Prevent further propagation

        ticket_label.bind("<Button-1>", toggle_issue)

        # Buttons for comments and delete
        btn_frame = tk.Frame(ticket_frame, bg=bg_color)
        btn_frame.pack(fill=tk.X, pady=5)

        comment_button = tk.Button(btn_frame, text="Comments", command=lambda t=ticket_data: self.show_comments(t),
                                   bg=self.button_color, fg=self.fg_color, activebackground=self.highlight_color)
        comment_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(btn_frame, text="Delete", fg="red", command=lambda t=ticket_data: self.delete_ticket_from_complete(t),
                                  bg=self.button_color, activebackground=self.highlight_color)
        delete_button.pack(side=tk.RIGHT, padx=5)

        # Bind click event to select ticket
        def select_ticket_event(event):
            self.select_ticket(ticket_data)
            return "break"  # Stop event propagation

        # Bind to ticket_frame and all widgets except ticket_label
        ticket_frame.bind("<Button-1>", select_ticket_event)
        for widget in ticket_frame.winfo_children():
            if widget != ticket_label:
                widget.bind("<Button-1>", select_ticket_event)

    def select_ticket(self, ticket_data):
        self.selected_ticket = ticket_data

        # Reset highlights in all containers
        for container, ticket_bg in [(self.open_container, self.open_ticket_bg),
                                     (self.in_progress_container, self.in_progress_ticket_bg),
                                     (self.complete_container, self.complete_ticket_bg)]:
            for widget in container.winfo_children():
                ticket_data_widget = widget.ticket_data
                priority = ticket_data_widget.get('Priority', 'Low').strip().lower()
                bg_color = self.high_priority_color if priority == 'high' else ticket_bg
                widget.config(bg=bg_color)
                for child in widget.winfo_children():
                    child.config(bg=bg_color)

        # Highlight the selected ticket in its container
        for container in [self.open_container, self.in_progress_container, self.complete_container]:
            for widget in container.winfo_children():
                if widget.ticket_data == ticket_data:
                    widget.config(bg=self.highlight_color)
                    for child in widget.winfo_children():
                        child.config(bg=self.highlight_color)
                    return

    # Modified move_to_in_progress to accept ticket_data
    def move_to_in_progress(self, ticket_data):
        if ticket_data is None:
            return

        # Check if the ticket is still in Open tickets
        if not any(ticket_data == t[0] for t in self.open_tickets):
            # Ticket is no longer in Open tickets
            return

        ticket_id = self.get_or_create_ticket_id(ticket_data)
        ticket_info = f"ID: {ticket_id}\n{ticket_data['Username']} - ({ticket_data['Time Placed']})"

        # Remove from Open tickets
        self.open_tickets = [t for t in self.open_tickets if t[0] != ticket_data]

        # Remove the ticket widget from the Open container
        for widget in self.open_container.winfo_children():
            if widget.ticket_data == ticket_data:
                widget.destroy()
                break

        # Add to In Progress tickets and display
        self.in_progress_tickets.append((ticket_data, ticket_info, ticket_id))
        self.add_ticket_to_in_progress(ticket_data, ticket_info, ticket_id)

        # Remove ticket from tickets.csv
        self.remove_ticket_from_csv(ticket_data)

        # Add ticket to in_progress_tickets.csv
        self.add_ticket_to_in_progress_csv(ticket_data)

    # Modified move_to_complete to accept ticket_data
    def move_to_complete(self, ticket_data):
        if ticket_data is None:
            return

        # Check if the ticket is still in In Progress tickets
        if not any(ticket_data == t[0] for t in self.in_progress_tickets):
            # Ticket is no longer in In Progress tickets
            return

        ticket_id = self.get_or_create_ticket_id(ticket_data)
        ticket_info = f"ID: {ticket_id}\n{ticket_data['Username']} - ({ticket_data['Time Placed']})"

        # Remove from In Progress tickets
        self.in_progress_tickets = [t for t in self.in_progress_tickets if t[0] != ticket_data]

        # Remove the ticket widget from the In Progress container
        for widget in self.in_progress_container.winfo_children():
            if widget.ticket_data == ticket_data:
                widget.destroy()
                break

        # Add to Complete tickets and display
        self.complete_tickets.append((ticket_data, ticket_info, ticket_id))
        self.add_ticket_to_complete(ticket_data, ticket_info, ticket_id)

        # Remove ticket from in_progress_tickets.csv
        self.remove_ticket_from_in_progress_csv(ticket_data)

        # Add ticket to completed_tickets.csv
        self.add_ticket_to_completed(ticket_data)

    # Update button click handlers to use the modified methods
    def move_to_in_progress_button_click(self):
        if hasattr(self, 'selected_ticket') and self.selected_ticket is not None:
            ticket_data = self.selected_ticket
            self.selected_ticket = None
            self.move_to_in_progress(ticket_data)

    def move_to_complete_button_click(self):
        if hasattr(self, 'selected_ticket') and self.selected_ticket is not None:
            ticket_data = self.selected_ticket
            self.selected_ticket = None
            self.move_to_complete(ticket_data)

    def delete_ticket(self):
        if not hasattr(self, 'selected_ticket') or self.selected_ticket is None:
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this ticket?")
        if not confirm:
            return

        ticket_data = self.selected_ticket
        self.selected_ticket = None  # Clear selected_ticket immediately
        ticket_id = self.get_or_create_ticket_id(ticket_data)

        # Remove from all ticket lists
        self.open_tickets = [t for t in self.open_tickets if t[0] != ticket_data]
        self.in_progress_tickets = [t for t in self.in_progress_tickets if t[0] != ticket_data]
        self.complete_tickets = [t for t in self.complete_tickets if t[0] != ticket_data]

        # Remove the ticket widget from all containers
        for container in [self.open_container, self.in_progress_container, self.complete_container]:
            for widget in container.winfo_children():
                if widget.ticket_data == ticket_data:
                    widget.destroy()
                    break

        # Remove ticket from CSV files
        self.remove_ticket_from_csv(ticket_data)
        self.remove_ticket_from_in_progress_csv(ticket_data)
        self.remove_ticket_from_completed_csv(ticket_data)

        # Remove comments associated with the ticket
        if ticket_id in self.comments:
            del self.comments[ticket_id]
            self.save_comments()

        # Remove ticket ID from tracking
        ticket_key = self.generate_ticket_key(ticket_data)
        if ticket_key in self.ticket_ids:
            del self.ticket_ids[ticket_key]
            self.save_ticket_ids()

    def delete_ticket_from_open(self, ticket_data):
        self.selected_ticket = ticket_data
        self.delete_ticket()

    def delete_ticket_from_in_progress(self, ticket_data):
        self.selected_ticket = ticket_data
        self.delete_ticket()

    def delete_ticket_from_complete(self, ticket_data):
        self.selected_ticket = ticket_data
        self.delete_ticket()

    def show_comments(self, ticket_data):
        ticket_id = self.get_or_create_ticket_id(ticket_data)
        existing_comments = self.comments.get(ticket_id, [])

        # Create a new window for comments
        comments_window = tk.Toplevel(self.master)
        comments_window.title(f"Comments - Ticket ID: {ticket_id}")
        comments_window.configure(bg=self.bg_color)

        # Display past comments in a Text widget (read-only)
        comments_label = tk.Label(comments_window, text="Past Comments:", font=("Arial", 12, "bold"), bg=self.bg_color, fg=self.fg_color)
        comments_label.pack(pady=5)

        comments_text = tk.Text(comments_window, width=60, height=15, wrap='word', bg=self.bg_color, fg=self.fg_color)
        comments_text.pack(padx=10, pady=5)
        comments_text.insert(tk.END, '\n\n'.join(existing_comments))
        comments_text.config(state=tk.DISABLED)  # Make it read-only

        # Entry for adding a new comment
        new_comment_label = tk.Label(comments_window, text="Add a New Comment:", font=("Arial", 12, "bold"), bg=self.bg_color, fg=self.fg_color)
        new_comment_label.pack(pady=5)

        new_comment_entry = tk.Text(comments_window, width=60, height=5, wrap='word', bg=self.bg_color, fg=self.fg_color)
        new_comment_entry.pack(padx=10, pady=5)

        # Button to save the new comment
        def save_new_comment():
            new_comment = new_comment_entry.get("1.0", tk.END).strip()
            if new_comment:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                formatted_comment = f"[{timestamp}] {new_comment}"
                existing_comments.append(formatted_comment)
                self.comments[ticket_id] = existing_comments
                self.save_comments()
                # Update the comments display
                comments_text.config(state=tk.NORMAL)
                comments_text.delete("1.0", tk.END)
                comments_text.insert(tk.END, '\n\n'.join(existing_comments))
                comments_text.config(state=tk.DISABLED)
                new_comment_entry.delete("1.0", tk.END)
            else:
                messagebox.showwarning("Empty Comment", "Please enter a comment before saving.")

        save_button = tk.Button(comments_window, text="Save Comment", command=save_new_comment,
                                bg=self.button_color, fg=self.fg_color, activebackground=self.highlight_color)
        save_button.pack(pady=10)

    def add_ticket_to_completed(self, ticket_data):
        fieldnames = ['Username', 'Issue', 'Time Placed', 'Priority']
        if not ticket_data or not all(field in ticket_data for field in fieldnames):
            print(f"Error: Invalid ticket_data {ticket_data}")
            return
        try:
            with open(COMPLETED_CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                # Write header only if file is empty
                if os.stat(COMPLETED_CSV_FILE).st_size == 0:
                    writer.writeheader()
                writer.writerow(ticket_data)
        except Exception as e:
            print(f"Error writing to {COMPLETED_CSV_FILE}: {e}")

    def add_ticket_to_in_progress_csv(self, ticket_data):
        fieldnames = ['Username', 'Issue', 'Time Placed', 'Priority']
        if not ticket_data or not all(field in ticket_data for field in fieldnames):
            print(f"Error: Invalid ticket_data {ticket_data}")
            return
        try:
            with open(IN_PROGRESS_CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                # Write header only if file is empty
                if os.stat(IN_PROGRESS_CSV_FILE).st_size == 0:
                    writer.writeheader()
                writer.writerow(ticket_data)
        except Exception as e:
            print(f"Error writing to {IN_PROGRESS_CSV_FILE}: {e}")

    def remove_ticket_from_csv(self, ticket_to_remove):
        # Read all tickets from the CSV file
        tickets = []
        fieldnames = []
        try:
            with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = reader.fieldnames
                for row in reader:
                    if not self.is_same_ticket(row, ticket_to_remove):
                        tickets.append(row)
        except FileNotFoundError:
            print(f"Error: CSV file not found at {CSV_FILE_PATH}")
            return

        # Write the updated list back to the CSV file
        try:
            with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tickets)
        except Exception as e:
            print(f"Error writing to {CSV_FILE_PATH}: {e}")

    def remove_ticket_from_in_progress_csv(self, ticket_to_remove):
        # Read all tickets from the in-progress CSV file
        tickets = []
        fieldnames = []
        try:
            with open(IN_PROGRESS_CSV_FILE, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = reader.fieldnames
                for row in reader:
                    if not self.is_same_ticket(row, ticket_to_remove):
                        tickets.append(row)
        except FileNotFoundError:
            return  # File may not exist yet

        # Write the updated list back to the in-progress CSV file
        try:
            with open(IN_PROGRESS_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tickets)
        except Exception as e:
            print(f"Error writing to {IN_PROGRESS_CSV_FILE}: {e}")

    def remove_ticket_from_completed_csv(self, ticket_to_remove):
        # Read all tickets from the completed CSV file
        tickets = []
        fieldnames = []
        try:
            with open(COMPLETED_CSV_FILE, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                fieldnames = reader.fieldnames
                for row in reader:
                    if not self.is_same_ticket(row, ticket_to_remove):
                        tickets.append(row)
        except FileNotFoundError:
            return  # File may not exist yet

        # Write the updated list back to the completed CSV file
        try:
            with open(COMPLETED_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tickets)
        except Exception as e:
            print(f"Error writing to {COMPLETED_CSV_FILE}: {e}")

    def is_same_ticket(self, ticket1, ticket2):
        # Compare Priority as well to maintain priority in data
        return (
            ticket1['Username'].strip().lower() == ticket2['Username'].strip().lower() and
            ticket1['Issue'].strip().lower() == ticket2['Issue'].strip().lower() and
            ticket1['Time Placed'].strip() == ticket2['Time Placed'].strip() and
            ticket1.get('Priority', '').strip().lower() == ticket2.get('Priority', '').strip().lower()
        )

    def read_completed_tickets(self):
        completed_tickets = {}
        try:
            with open(COMPLETED_CSV_FILE, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    ticket_id = self.get_or_create_ticket_id(row)
                    ticket_info = f"ID: {ticket_id}\n{row['Username']} - ({row['Time Placed']})"
                    completed_tickets[ticket_id] = {'ticket_data': row, 'ticket_info': ticket_info}
        except FileNotFoundError:
            pass  # No completed tickets yet
        return completed_tickets

    def read_in_progress_tickets(self):
        in_progress_tickets = {}
        try:
            with open(IN_PROGRESS_CSV_FILE, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    ticket_id = self.get_or_create_ticket_id(row)
                    ticket_info = f"ID: {ticket_id}\n{row['Username']} - ({row['Time Placed']})"
                    in_progress_tickets[ticket_id] = {'ticket_data': row, 'ticket_info': ticket_info}
        except FileNotFoundError:
            pass  # No in-progress tickets yet
        return in_progress_tickets

    def start_auto_refresh(self):
        self.master.after(30000, self.load_tickets)  # Schedule the first refresh in 30 seconds

if __name__ == "__main__":
    root = tk.Tk()
    app = TicketTracker(root)
    root.mainloop()

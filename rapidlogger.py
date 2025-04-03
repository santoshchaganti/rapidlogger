import tkinter as tk
from tkinter import ttk
import csv
from datetime import datetime
import os

class Colors:
    """Color constants for the application theme"""
    BG = '#000000'
    FG = '#ffffff'
    ENTRY_BG = '#3b3b3b'
    BUTTON_BG = '#404040'
    BUTTON_HOVER = '#505050'
    TITLE_BG = '#000000'
    BUTTON_ACTIVE_BG = '#505050'
    BUTTON_ACTIVE_FG = '#ffffff'
    CLOSE_HOVER = '#bf0000'

class OverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RapidLogger")
        
        # Make window appear in taskbar and Alt+Tab
        self.root.wm_attributes('-toolwindow', 0)
        
        # Initialize file paths
        self.csv_file = "data_log.csv"
        self.html_file = "data_log.html"
        self.initialize_files()
        
        # Configure the root window
        self.root.configure(bg=Colors.BG)
        
        # Remove default title bar and make window transparent and always on top
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.95)
        self.root.attributes('-topmost', True)
        
        # Create and configure style for dark theme
        self.style = ttk.Style()
        self.style.configure('Dark.TFrame', background=Colors.BG)
        self.style.configure('Dark.TLabel', 
                           background=Colors.BG, 
                           foreground=Colors.FG)
        
        self._create_title_bar()
        self._create_main_frame()
        self._create_input_fields()
        self._create_buttons()
        
        # Setup keyboard shortcuts
        self.root.bind('<Return>', self.handle_return)
        self.root.bind('<Escape>', lambda e: self.minimize_window())
        
        # Initial window position (bottom right)
        self.position_window()
        
    def _create_title_bar(self):
        """Create the custom title bar"""
        self.title_bar = tk.Frame(self.root, bg=Colors.TITLE_BG, height=30)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.bind('<Button-1>', self.start_move)
        self.title_bar.bind('<B1-Motion>', self.on_move)
        
        # Add title label
        self.title_label = tk.Label(self.title_bar, text="RapidLogger", 
                                  bg=Colors.TITLE_BG, fg=Colors.FG)
        self.title_label.pack(side=tk.LEFT, padx=10)
        self.title_label.bind('<Button-1>', self.start_move)
        self.title_label.bind('<B1-Motion>', self.on_move)
        
        # Create close button
        self.close_button = tk.Button(self.title_bar, text='✕', 
                                    command=self.root.quit, 
                                    bg=Colors.TITLE_BG, 
                                    fg=Colors.FG,
                                    bd=0, padx=10,
                                    activebackground=Colors.CLOSE_HOVER,
                                    activeforeground=Colors.FG)
        self.close_button.pack(side=tk.RIGHT)
        self.close_button.bind('<Enter>', lambda e: e.widget.config(bg=Colors.CLOSE_HOVER))
        self.close_button.bind('<Leave>', lambda e: e.widget.config(bg=Colors.TITLE_BG))

    def _create_main_frame(self):
        """Create the main application frame"""
        self.main_frame = ttk.Frame(self.root, padding="10", style='Dark.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def _create_input_fields(self):
        """Create the input fields with labels"""
        # First input frame
        self.input_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        self.input_frame.pack(fill=tk.X, pady=5)
        
        self.input1_label = ttk.Label(self.input_frame, text="Comp:", 
                                    style='Dark.TLabel', width=6, anchor='w')
        self.input1_label.pack(side=tk.LEFT, padx=(0, 10))
        self.input1 = tk.Entry(self.input_frame, width=30,
                             bg=Colors.ENTRY_BG,
                             fg=Colors.FG,
                             insertbackground=Colors.FG)
        self.input1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Second input frame
        self.input2_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        self.input2_frame.pack(fill=tk.X, pady=5)
        
        self.input2_label = ttk.Label(self.input2_frame, text="Link:",
                                    style='Dark.TLabel', width=6, anchor='w')
        self.input2_label.pack(side=tk.LEFT, padx=(0, 10))
        self.input2 = tk.Entry(self.input2_frame, width=30,
                             bg=Colors.ENTRY_BG,
                             fg=Colors.FG,
                             insertbackground=Colors.FG)
        self.input2.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _create_button(self, parent, text, command):
        """Create a standardized button with hover effects"""
        button = tk.Button(parent, text=text,
                         command=command,
                         bg=Colors.BUTTON_BG,
                         fg=Colors.FG,
                         activebackground=Colors.BUTTON_ACTIVE_BG,
                         activeforeground=Colors.BUTTON_ACTIVE_FG,
                         relief='flat',
                         width=10,
                         borderwidth=1)
        button.bind('<Enter>', lambda e: e.widget.config(bg=Colors.BUTTON_HOVER))
        button.bind('<Leave>', lambda e: e.widget.config(bg=Colors.BUTTON_BG))
        return button

    def _create_buttons(self):
        """Create all action buttons"""
        self.button_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # Create buttons using the helper method
        self.send_button = self._create_button(self.button_frame, "Send", self.save_data)
        self.send_button.pack(side=tk.LEFT, padx=5, expand=True)
        
        self.refresh_button = self._create_button(self.button_frame, "Refresh", self.refresh_view)
        self.refresh_button.pack(side=tk.LEFT, padx=5, expand=True)

    def position_window(self):
        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate window size
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Position window in middle-right with padding
        x = screen_width - window_width - 30
        y = (screen_height - window_height) // 2  # Center vertically
        
        self.root.geometry(f"+{x}+{y}")
    
    def handle_return(self, event):
        # If focus is on company field, move to link field
        if self.root.focus_get() == self.input1:
            self.input2.focus_set()
        # If focus is on link field, save the data and flash the send button
        elif self.root.focus_get() == self.input2:
            self.flash_button(self.send_button)
            self.save_data()
            # Return focus to company field for next entry
            self.input1.focus_set()
    
    def minimize_window(self):
        self.root.iconify()
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def initialize_files(self):
        # Initialize CSV file
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Company Name", "Applied Job Link", "Status"])
        
        # Initialize HTML file with style
        if not os.path.exists(self.html_file):
            self.update_html_file([])

    def refresh_view(self):
        """Refresh the HTML view from the current CSV data"""
        self.update_html_file()
        # Optional: Open the HTML file in the default browser
        import webbrowser
        webbrowser.open(self.html_file)

    def update_html_file(self, new_row=None):
        # Read existing CSV data
        data = []
        if os.path.exists(self.csv_file):
            with open(self.csv_file, 'r', newline='') as file:
                reader = csv.reader(file)
                data = list(reader)
        
        # Add new row if provided
        if new_row and not data:
            data.append(["Date", "Company Name", "Applied Job Link", "Status"])
        if new_row:
            data.append(new_row)
        
        # Create HTML content with modern styling
        html_content = """
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    background-color: white;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                }
                th, td {
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background-color: #4a4a4a;
                    color: white;
                }
                tr:hover {
                    background-color: #f5f5f5;
                }
                a {
                    color: #2196F3;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
                .status {
                    padding: 5px 10px;
                    border-radius: 15px;
                    color: white;
                    display: inline-block;
                }
                .Applied {
                    background-color: #2196F3;
                }
                .Interview {
                    background-color: #FF9800;
                }
                .Rejected {
                    background-color: #f44336;
                }
                .Accepted {
                    background-color: #4CAF50;
                }
            </style>
        </head>
        <body>
            <table>
        """
        
        # Add table content
        for i, row in enumerate(data):
            if i == 0:  # Header row
                html_content += "<tr>"
                for cell in row:
                    html_content += f"<th>{cell}</th>"
                html_content += "</tr>"
            else:  # Data rows
                html_content += "<tr>"
                for j, cell in enumerate(row):
                    if j == 2:  # Link column
                        html_content += f'<td><a href="{cell}" target="_blank">{cell}</a></td>'
                    elif j == 3:  # Status column
                        status_class = cell.replace(" ", "")  # Remove spaces for CSS class
                        html_content += f'<td><span class="status {status_class}">{cell}</span></td>'
                    else:
                        html_content += f"<td>{cell}</td>"
                html_content += "</tr>"
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        # Write HTML file
        with open(self.html_file, 'w', encoding='utf-8') as file:
            file.write(html_content)

    def save_data(self):
        input1_value = self.input1.get()
        input2_value = self.input2.get()
        
        if not input1_value or not input2_value:
            return
        
        # Prepare row data
        new_row = [
            datetime.now().strftime("%d-%m"),
            input1_value,
            input2_value,
            "Applied"
        ]
        
        # Save to CSV
        with open(self.csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(new_row)
        
        # Update HTML file
        self.update_html_file(new_row)
        
        # Clear input fields
        self.input1.delete(0, tk.END)
        self.input2.delete(0, tk.END)

    def flash_button(self, button):
        """Creates a quick flash effect on the button"""
        original_color = button.cget('bg')
        button.config(bg='#606060')
        self.root.after(100, lambda: button.config(bg=original_color))

if __name__ == "__main__":
    root = tk.Tk()
    app = OverlayApp(root)
    root.mainloop() 
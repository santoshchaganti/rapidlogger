import tkinter as tk
from tkinter import ttk
import csv
from datetime import datetime
import os

class OverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RapidLogger")
        
        # Make window appear in taskbar and Alt+Tab
        self.root.wm_attributes('-toolwindow', 0)
        
        # Configure dark theme colors
        self.bg_color = '#2b2b2b'
        self.fg_color = '#ffffff'
        self.entry_bg = '#3b3b3b'
        self.button_bg = '#404040'
        self.button_hover = '#4a4a4a'
        self.title_bg = '#1e1e1e'  # Darker color for title bar
        
        # Initialize file paths
        self.csv_file = "data_log.csv"
        self.html_file = "data_log.html"
        self.initialize_files()
        
        # Configure the root window
        self.root.configure(bg=self.bg_color)
        
        # Remove default title bar and make window transparent and always on top
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.95)
        self.root.attributes('-topmost', True)
        
        # Create and configure style for dark theme
        self.style = ttk.Style()
        self.style.configure('Dark.TFrame', background=self.bg_color)
        self.style.configure('Dark.TLabel', 
                           background=self.bg_color, 
                           foreground=self.fg_color)
        
        # Create title bar frame
        self.title_bar = tk.Frame(self.root, bg=self.title_bg, height=30)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.bind('<Button-1>', self.start_move)
        self.title_bar.bind('<B1-Motion>', self.on_move)
        
        # Add title label without emoji
        self.title_label = tk.Label(self.title_bar, text="RapidLogger", bg=self.title_bg, fg='white')
        self.title_label.pack(side=tk.LEFT, padx=10)
        self.title_label.bind('<Button-1>', self.start_move)
        self.title_label.bind('<B1-Motion>', self.on_move)
        
        # Create close button
        self.close_button = tk.Button(self.title_bar, text='✕', command=self.root.quit, 
                                    bg=self.title_bg, fg='white', bd=0, padx=10,
                                    activebackground='#bf0000', activeforeground='white')
        self.close_button.pack(side=tk.RIGHT)
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10", style='Dark.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create input fields frame
        self.input_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        self.input_frame.pack(fill=tk.X, pady=5)
        
        # Create input fields with left-aligned labels
        self.input1_label = ttk.Label(self.input_frame, text="Comp:", style='Dark.TLabel', width=6, anchor='w')
        self.input1_label.pack(side=tk.LEFT, padx=(0, 10))
        self.input1 = tk.Entry(self.input_frame, width=30, 
                             bg=self.entry_bg, fg=self.fg_color,
                             insertbackground=self.fg_color)
        self.input1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Create second input frame
        self.input2_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        self.input2_frame.pack(fill=tk.X, pady=5)
        
        self.input2_label = ttk.Label(self.input2_frame, text="Link:", style='Dark.TLabel', width=6, anchor='w')
        self.input2_label.pack(side=tk.LEFT, padx=(0, 10))
        self.input2 = tk.Entry(self.input2_frame, width=30,
                             bg=self.entry_bg, fg=self.fg_color,
                             insertbackground=self.fg_color)
        self.input2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Create button frame for horizontal layout
        self.button_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # Create send button with hover binding
        self.send_button = tk.Button(self.button_frame, text="Send", 
                                   command=self.save_data,
                                   bg=self.button_bg,
                                   fg=self.fg_color,
                                   activebackground='#505050',
                                   activeforeground='#ffffff',
                                   relief='flat',
                                   width=10,
                                   borderwidth=1)
        self.send_button.pack(side=tk.LEFT, padx=5, expand=True)
        self.send_button.bind('<Enter>', lambda e: e.widget.config(bg='#505050'))
        self.send_button.bind('<Leave>', lambda e: e.widget.config(bg=self.button_bg))
        
        # Create refresh button with hover binding
        self.refresh_button = tk.Button(self.button_frame, text="Refresh", 
                                    command=self.refresh_view,
                                    bg=self.button_bg,
                                    fg=self.fg_color,
                                    activebackground='#505050',
                                    activeforeground='#ffffff',
                                    relief='flat',
                                    width=10,
                                    borderwidth=1)
        self.refresh_button.pack(side=tk.LEFT, padx=5, expand=True)
        self.refresh_button.bind('<Enter>', lambda e: e.widget.config(bg='#505050'))
        self.refresh_button.bind('<Leave>', lambda e: e.widget.config(bg=self.button_bg))
        
        # Create close button with hover binding
        self.close_button = tk.Button(self.button_frame, text="Close", 
                                    command=self.root.quit,
                                    bg=self.button_bg,
                                    fg=self.fg_color,
                                    activebackground='#505050',
                                    activeforeground='#ffffff',
                                    relief='flat',
                                    width=10,
                                    borderwidth=1)
        self.close_button.pack(side=tk.LEFT, padx=5, expand=True)
        self.close_button.bind('<Enter>', lambda e: e.widget.config(bg='#505050'))
        self.close_button.bind('<Leave>', lambda e: e.widget.config(bg=self.button_bg))
        
        # Setup keyboard shortcuts
        self.root.bind('<Return>', lambda e: self.handle_return(e))
        self.root.bind('<Escape>', lambda e: self.minimize_window())
        
        # Initial window position (bottom right)
        self.position_window()
        
        # Register in taskbar
        self.root.after(10, lambda: self.root.state('normal'))
        
    def position_window(self):
        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate window size
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Position window in bottom right corner with some padding
        x = screen_width - window_width - 20
        y = screen_height - window_height - 40
        
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
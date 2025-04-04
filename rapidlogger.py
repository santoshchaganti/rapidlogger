import tkinter as tk
from tkinter import ttk
import csv
from datetime import datetime
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from urllib.parse import parse_qs
import logging
import sys

# Setup logging
log_file = 'rapidlogger.log'
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Redirect stderr to log file
sys.stderr = open(log_file, 'a')

class StatusUpdateHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Redirect server logs to our log file
        logging.info(format%args)

    def do_POST(self):
        if self.path == '/update_status':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            success = self.server.app.update_status(data['id'], data['status'])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({'success': success})
            self.wfile.write(response.encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

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

class RapidLogger:
    def __init__(self, root):
        self.root = root
        self.root.title("RapidLogger")
        
        # Start HTTP server
        self.start_http_server()
        
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
                writer.writerow(["ID", "Date", "Company Name", "Applied Job Link", "Status"])
        
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
            data.append(["ID", "Date", "Company Name", "Applied Job Link", "Status"])
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
                    background-color: #FFF8E7;
                    color: #333;
                }
                .stats-panel {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                    gap: 10px;
                    margin-bottom: 16px;
                }
                .stat-card {
                    background: white;
                    padding: 12px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    border: 1px solid rgba(226, 232, 240, 0.8);
                    position: relative;
                    overflow: hidden;
                }
                .stat-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                }
                /* Card top borders colors */
                .stat-card:nth-child(1)::before {
                    background: #60A5FA;  /* Blue */
                }
                .stat-card:nth-child(2)::before {
                    background: #A78BFA;  /* Purple */
                }
                .stat-card:nth-child(3)::before {
                    background: #34D399;  /* Teal */
                }
                .stat-card:nth-child(4)::before {
                    background: #FB923C;  /* Orange */
                }
                .stat-card:nth-child(5)::before {
                    background: #60A5FA;  /* Blue */
                }
                /* Value colors matching the borders */
                #todayCount {
                    color: #60A5FA;  /* Blue */
                }
                #totalCount {
                    color: #A78BFA;  /* Purple */
                }
                #interviewCount {
                    color: #34D399;  /* Teal */
                }
                #responseRate {
                    color: #FB923C;  /* Orange */
                }
                .stat-header {
                    display: flex;
                    align-items: center;
                    gap: 5px;
                    margin-bottom: 8px;
                }
                .stat-icon {
                    width: 14px;
                    height: 14px;
                    opacity: 0.8;
                }
                .stat-title {
                    color: #475569;
                    font-size: 12px;
                    font-weight: 600;
                    letter-spacing: 0.2px;
                }
                .stat-value {
                    font-size: 24px;
                    font-weight: 600;
                    margin: 3px 0;
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    letter-spacing: -0.3px;
                }
                .stat-subtext {
                    color: #94A3B8;
                    font-size: 11px;
                    line-height: 1.3;
                }
                .trend-card {
                    background: white;
                    padding: 12px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    border: 1px solid rgba(226, 232, 240, 0.8);
                    position: relative;
                    overflow: hidden;
                }
                .trend-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: #60A5FA;  /* Blue */
                }
                .trend-title {
                    color: #475569;
                    font-size: 13px;
                    font-weight: 600;
                    margin-bottom: 8px;
                    letter-spacing: 0.3px;
                }
                .trend-bars {
                    display: flex;
                    align-items: flex-end;
                    gap: 3px;
                    height: 25px;
                    margin-top: 12px;
                }
                .trend-bar {
                    flex: 1;
                    background: #e2e8f0;
                    border-radius: 3px;
                    position: relative;
                    min-height: 3px;
                    transition: all 0.3s ease;
                }
                .trend-bar-fill {
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    width: 100%;
                    background: #2563eb;
                    border-radius: 3px;
                    transition: height 0.3s ease;
                }
                .trend-bar-count {
                    position: absolute;
                    top: -14px;
                    left: 50%;
                    transform: translateX(-50%);
                    font-size: 10px;
                    color: #475569;
                    font-weight: 600;
                }
                .trend-dates {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 4px;
                    color: #64748b;
                    font-size: 9px;
                }
                .controls {
                    padding: 0 0 10px 0;
                    display: flex;
                    gap: 20px;
                    align-items: center;
                }
                .pagination {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 20px 0;
                    gap: 10px;
                }
                .pagination button {
                    padding: 8px 12px;
                    border: 2px solid #E2E8F0;
                    background: white;
                    color: #2c3e50;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: all 0.2s ease;
                }
                .pagination button:hover {
                    border-color: #6D9DC5;
                    background: #F8FAFC;
                }
                .pagination button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                    border-color: #E2E8F0;
                }
                .pagination-info {
                    color: #64748B;
                    font-size: 14px;
                }
                .search-container {
                    flex: 1;
                    position: relative;
                }
                .search-container::before {
                    content: '';
                    position: absolute;
                    left: 12px;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 16px;
                    height: 16px;
                    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'%3E%3C/circle%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'%3E%3C/line%3E%3C/svg%3E");
                    background-repeat: no-repeat;
                    background-position: center;
                    opacity: 0.8;
                }
                .search-box {
                    width: 100%;
                    padding: 10px 10px 10px 35px;
                    border: 2px solid #E2E8F0;
                    border-radius: 20px;
                    font-size: 14px;
                    outline: none;
                    transition: all 0.2s ease;
                    background-color: white;
                    color: #2c3e50;
                }
                .search-box::placeholder {
                    color: #94A3B8;
                    opacity: 0.7;
                }
                .search-box:hover {
                    border-color: #CBD5E1;
                }
                .search-box:focus {
                    border-color: #6D9DC5;
                    box-shadow: 0 2px 8px rgba(109, 157, 197, 0.15);
                }
                .filter-select {
                    padding: 10px 35px 10px 15px;
                    border: 2px solid #E2E8F0;
                    border-radius: 20px;
                    font-size: 14px;
                    outline: none;
                    min-width: 140px;
                    cursor: pointer;
                    background-color: white;
                    color: #2c3e50;
                    transition: all 0.2s ease;
                    appearance: none;
                    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
                    background-repeat: no-repeat;
                    background-position: right 10px center;
                    background-size: 16px;
                }
                .filter-select:hover {
                    border-color: #CBD5E1;
                }
                .filter-select:focus {
                    border-color: #6D9DC5;
                    box-shadow: 0 2px 8px rgba(109, 157, 197, 0.15);
                }
                table {
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    background-color: white;
                    box-shadow: 0 2px 15px rgba(0,0,0,0.1);
                    margin-top: 10px;
                    border-radius: 8px;
                    overflow: hidden;
                    font-size: 13px;
                }
                th, td {
                    padding: 10px 15px;
                    text-align: center;
                    border-bottom: 1px solid #E2E8F0;
                    transition: background-color 0.2s ease;
                }
                th {
                    background-color: #2A4365;
                    color: white;
                    font-weight: 600;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    padding: 12px 15px;
                }
                tr:last-child td {
                    border-bottom: none;
                }
                tr:hover td {
                    background-color: #F5F6F7;
                }
                td:first-child {
                    width: 50px;
                    font-weight: 600;
                    color: #2c3e50;
                }
                td:nth-child(2) {
                    width: 80px;
                    color: #666;
                }
                td:nth-child(3) {
                    min-width: 150px;
                }
                td:nth-child(4) {
                    min-width: 200px;
                }
                td:last-child {
                    width: 120px;
                }
                a {
                    color: #3498db;
                    text-decoration: none;
                    transition: color 0.2s ease;
                    display: inline-block;
                    max-width: 300px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    font-size: 13px;
                }
                a:hover {
                    color: #2980b9;
                    text-decoration: none;
                }
                .status-select {
                    width: 100%;
                    padding: 6px 10px;
                    border-radius: 15px;
                    border: none;
                    font-size: 13px;
                    color: white;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    outline: none;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .status-select:hover {
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                }
                .status-select option {
                    background-color: white;
                    color: #333;
                    padding: 10px;
                }
                .Applied { background-color: #6D9DC5; }
                .Interview { background-color: #9D8EC7; }
                .Rejected { background-color: #FF7F6B; }
                .Accepted { background-color: #5CBDB9; }
            </style>
            <script>
                // Search and filter functionality
                function filterTable() {
                    const searchText = document.getElementById('searchBox').value.toLowerCase();
                    const statusFilter = document.getElementById('statusFilter').value;
                    const rows = document.querySelectorAll('tbody tr');
                    let visibleRows = [];
                    
                    rows.forEach(row => {
                        const companyName = row.cells[2].textContent.toLowerCase();
                        const statusSelect = row.cells[4].querySelector('select');
                        const status = statusSelect ? statusSelect.value : '';
                        const matchesSearch = companyName.includes(searchText);
                        const matchesStatus = statusFilter === 'All' || status === statusFilter;
                        
                        if (matchesSearch && matchesStatus) {
                            visibleRows.push(row);
                        }
                        row.style.display = 'none';
                    });

                    // Update pagination
                    currentPage = 1;
                    totalPages = Math.ceil(visibleRows.length / rowsPerPage);
                    showPage(visibleRows);
                    updatePaginationControls(visibleRows.length);
                }

                let currentPage = 1;
                const rowsPerPage = 50;
                let totalPages = 1;

                function showPage(visibleRows) {
                    const start = (currentPage - 1) * rowsPerPage;
                    const end = start + rowsPerPage;
                    
                    visibleRows.forEach((row, index) => {
                        if (index >= start && index < end) {
                            row.style.display = '';
                        } else {
                            row.style.display = 'none';
                        }
                    });
                }

                function updatePaginationControls(totalRows) {
                    const paginationInfo = document.getElementById('paginationInfo');
                    const prevButton = document.getElementById('prevPage');
                    const nextButton = document.getElementById('nextPage');
                    
                    totalPages = Math.ceil(totalRows / rowsPerPage);
                    
                    paginationInfo.textContent = `Page ${currentPage} of ${totalPages} (${totalRows} entries)`;
                    prevButton.disabled = currentPage === 1;
                    nextButton.disabled = currentPage === totalPages || totalRows === 0;
                }

                function changePage(delta) {
                    const newPage = currentPage + delta;
                    if (newPage >= 1 && newPage <= totalPages) {
                        currentPage = newPage;
                        filterTable();
                    }
                }

                function calculateStats() {
                    const rows = document.querySelectorAll('tbody tr');
                    const today = new Date();
                    
                    // Initialize counters
                    let todayCount = 0;
                    let totalCount = 0;
                    let statusCounts = {
                        'Applied': 0,
                        'Interview': 0,
                        'Accepted': 0,
                        'Rejected': 0
                    };
                    
                    // Initialize past 10 days counts
                    let pastDaysCounts = Array(10).fill(0);
                    let pastDaysLabels = Array(10).fill('');
                    
                    // Calculate dates for past 10 days
                    for(let i = 0; i < 10; i++) {
                        const date = new Date(today);
                        date.setDate(date.getDate() - i);
                        pastDaysLabels[9-i] = date.getDate() + '/' + (date.getMonth() + 1);
                    }
                    
                    rows.forEach(row => {
                        const dateCell = row.cells[1].textContent;
                        const statusSelect = row.cells[4].querySelector('select');
                        const status = statusSelect ? statusSelect.value : '';
                        
                        // Count today's applications
                        const [day, month] = dateCell.split('-').map(Number);
                        const currentDate = new Date();
                        
                        // Check for applications in past 10 days
                        for(let i = 0; i < 10; i++) {
                            const checkDate = new Date(today);
                            checkDate.setDate(checkDate.getDate() - i);
                            if(day === checkDate.getDate() && month === checkDate.getMonth() + 1) {
                                pastDaysCounts[9-i]++;
                                if(i === 0) todayCount++;
                                break;
                            }
                        }
                        
                        // Count by status
                        if (status in statusCounts) {
                            statusCounts[status]++;
                        }
                        
                        totalCount++;
                    });
                    
                    // Calculate response rate
                    const responseRate = totalCount > 0 
                        ? Math.round((statusCounts['Interview'] + statusCounts['Accepted']) / totalCount * 100) 
                        : 0;
                    
                    // Update stats in the DOM
                    document.getElementById('todayCount').textContent = todayCount;
                    document.getElementById('totalCount').textContent = totalCount;
                    document.getElementById('interviewCount').textContent = statusCounts['Interview'];
                    document.getElementById('responseRate').textContent = responseRate + '%';
                    
                    // Update trend bars
                    const maxCount = Math.max(...pastDaysCounts.slice(-5), 1);
                    const trendBars = document.querySelectorAll('.trend-bar');
                    const trendDates = document.querySelectorAll('.trend-date');
                    
                    trendBars.forEach((bar, index) => {
                        const count = pastDaysCounts[pastDaysCounts.length - 5 + index];
                        const height = (count / maxCount) * 100;
                        const fill = bar.querySelector('.trend-bar-fill');
                        const countElement = bar.querySelector('.trend-bar-count');
                        
                        fill.style.height = `${Math.max(height, 4)}%`;
                        countElement.textContent = count;
                        
                        // Update date labels
                        trendDates[index].textContent = pastDaysLabels[pastDaysLabels.length - 5 + index];
                    });
                }

                // Initialize pagination and filtering
                document.addEventListener('DOMContentLoaded', function() {
                    // Add input handlers for filtering
                    document.getElementById('searchBox').addEventListener('input', filterTable);
                    document.getElementById('statusFilter').addEventListener('change', filterTable);
                    
                    // Initial calculations
                    calculateStats();
                    filterTable();
                });

                function updateStatus(selectElement) {
                    const id = selectElement.getAttribute('data-id');
                    const newStatus = selectElement.value;
                    selectElement.className = 'status-select ' + newStatus;
                    
                    // Send update to server
                    fetch('http://localhost:8000/update_status', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            id: id,
                            status: newStatus
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (!data.success) {
                            alert('Failed to update status');
                        }
                        // Recalculate stats and refresh filters
                        calculateStats();
                        filterTable();
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Error updating status');
                    });
                }
            </script>
        </head>
        <body>
            <div class="stats-panel">
                <div class="stat-card">
                    <div class="stat-info">
                        <div class="stat-header">
                            <svg class="stat-icon" fill="none" stroke="#60A5FA" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                            <div class="stat-title">Today's Applications</div>
                        </div>
                        <div class="stat-value" id="todayCount">0</div>
                        <div class="stat-subtext">Applications submitted today</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-info">
                        <div class="stat-header">
                            <svg class="stat-icon" fill="none" stroke="#A78BFA" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                            </svg>
                            <div class="stat-title">Total Applications</div>
                        </div>
                        <div class="stat-value" id="totalCount">0</div>
                        <div class="stat-subtext">Total jobs applied</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-info">
                        <div class="stat-header">
                            <svg class="stat-icon" fill="none" stroke="#34D399" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                            </svg>
                            <div class="stat-title">Interviews</div>
                        </div>
                        <div class="stat-value" id="interviewCount">0</div>
                        <div class="stat-subtext">Interview invitations</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-info">
                        <div class="stat-header">
                            <svg class="stat-icon" fill="none" stroke="#FB923C" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                            </svg>
                            <div class="stat-title">Response Rate</div>
                        </div>
                        <div class="stat-value" id="responseRate">0%</div>
                        <div class="stat-subtext">Interview/Acceptance rate</div>
                    </div>
                </div>
                <div class="trend-card">
                    <div class="stat-header">
                        <svg class="stat-icon" fill="none" stroke="#60A5FA" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                        </svg>
                        <div class="stat-title">Last 5 Days Applications</div>
                    </div>
                    <div class="trend-bars">
                        <div class="trend-bar">
                            <div class="trend-bar-count">0</div>
                            <div class="trend-bar-fill"></div>
                        </div>
                        <div class="trend-bar">
                            <div class="trend-bar-count">0</div>
                            <div class="trend-bar-fill"></div>
                        </div>
                        <div class="trend-bar">
                            <div class="trend-bar-count">0</div>
                            <div class="trend-bar-fill"></div>
                        </div>
                        <div class="trend-bar">
                            <div class="trend-bar-count">0</div>
                            <div class="trend-bar-fill"></div>
                        </div>
                        <div class="trend-bar">
                            <div class="trend-bar-count">0</div>
                            <div class="trend-bar-fill"></div>
                        </div>
                    </div>
                    <div class="trend-dates">
                        <span class="trend-date"></span>
                        <span class="trend-date"></span>
                        <span class="trend-date"></span>
                        <span class="trend-date"></span>
                        <span class="trend-date"></span>
                    </div>
                </div>
            </div>
            <div class="controls">
                <div class="search-container">
                    <input type="text" id="searchBox" class="search-box" placeholder="Search by company name...">
                </div>
                <select id="statusFilter" class="filter-select">
                    <option value="All">All Status</option>
                    <option value="Applied">Applied</option>
                    <option value="Interview">Interview</option>
                    <option value="Accepted">Accepted</option>
                    <option value="Rejected">Rejected</option>
                </select>
            </div>
            <table>
                <thead>
                    <tr>
        """
        
        # Add headers
        for cell in data[0]:
            html_content += f"<th>{cell}</th>"
        
        html_content += """
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add table content
        for i, row in enumerate(data):
            if i > 0:  # Skip header row
                html_content += "<tr>"
                for j, cell in enumerate(row):
                    if j == 3:  # Link column
                        html_content += f'<td><a href="{cell}" target="_blank">{cell}</a></td>'
                    elif j == 4:  # Status column
                        current_status = cell
                        html_content += f'''
                        <td>
                            <select class="status-select {current_status}" data-id="{row[0]}" onchange="updateStatus(this)">
                                <option value="Applied" {"selected" if current_status == "Applied" else ""}>Applied</option>
                                <option value="Interview" {"selected" if current_status == "Interview" else ""}>Interview</option>
                                <option value="Accepted" {"selected" if current_status == "Accepted" else ""}>Accepted</option>
                                <option value="Rejected" {"selected" if current_status == "Rejected" else ""}>Rejected</option>
                            </select>
                        </td>'''
                    else:
                        html_content += f"<td>{cell}</td>"
                html_content += "</tr>"
        
        html_content += """
                </tbody>
            </table>
            <div class="pagination">
                <button id="prevPage" onclick="changePage(-1)">&lt; Previous</button>
                <span id="paginationInfo" class="pagination-info">Page 1 of 1</span>
                <button id="nextPage" onclick="changePage(1)">Next &gt;</button>
            </div>
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
        
        # Get the next ID
        next_id = 1
        existing_data = []
        
        if os.path.exists(self.csv_file):
            with open(self.csv_file, 'r', newline='') as file:
                reader = csv.reader(file)
                existing_data = list(reader)
                if len(existing_data) > 1:  # If there's data beyond header
                    next_id = max(int(row[0]) for row in existing_data[1:]) + 1
        
        # Prepare row data
        new_row = [
            next_id,
            datetime.now().strftime("%d-%m"),
            input1_value,
            input2_value,
            "Applied"
        ]
        
        # Insert new row after header
        if not existing_data:
            existing_data = [["ID", "Date", "Company Name", "Applied Job Link", "Status"]]
        existing_data.insert(1, new_row)  # Insert after header
        
        # Save to CSV
        with open(self.csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(existing_data)
        
        # Update HTML file
        self.update_html_file()
        
        # Clear input fields
        self.input1.delete(0, tk.END)
        self.input2.delete(0, tk.END)

    def flash_button(self, button):
        """Creates a quick flash effect on the button"""
        original_color = button.cget('bg')
        button.config(bg='#606060')
        self.root.after(100, lambda: button.config(bg=original_color))

    def start_http_server(self):
        """Start the HTTP server in a separate thread"""
        try:
            server = HTTPServer(('localhost', 8000), StatusUpdateHandler)
            server.app = self  # Store reference to app instance
            thread = threading.Thread(target=server.serve_forever)
            thread.daemon = True  # Thread will close when main program exits
            thread.start()
            logging.info("RapidLogger HTTP server started successfully on port 8000")
        except Exception as e:
            logging.error(f"Error starting HTTP server: {e}")
            logging.error("The application will continue to run, but status updates may not work")

    def update_status(self, row_id, new_status):
        """Update the status in the CSV file"""
        try:
            # Read all data
            with open(self.csv_file, 'r', newline='') as file:
                reader = csv.reader(file)
                data = list(reader)
            
            # Find and update the row
            for row in data:
                if row[0] == str(row_id):
                    row[4] = new_status
                    break
            
            # Write back to CSV
            with open(self.csv_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(data)
            
            # Update HTML
            self.update_html_file()
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = RapidLogger(root)
        logging.info("RapidLogger application started successfully")
        root.mainloop()
    except Exception as e:
        logging.error(f"Error in main application: {e}")
        input("Press Enter to exit...")
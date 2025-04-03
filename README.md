# RapidLogger

A minimal, efficient job application tracker that stays out of your way. Perfect for quickly logging job applications while you're actively applying.

## Features

- **Quick Entry**: Two-field interface for Company and Link
- **Keyboard Navigation**: 
  - Tab/Enter to move between fields
  - Enter to save entry
- **Data Storage**:
  - CSV file (`data_log.csv`) for data persistence
  - HTML file (`data_log.html`) with clickable links
- **Dark Theme**: Easy on the eyes with a professional dark interface
- **Always On Top**: Window stays visible while applying to jobs
- **Draggable**: Move the window by dragging the title bar
- **Status Tracking**: Automatically marks entries as "Applied"

## Usage

1. Double-click `launch_rapidlogger.bat` to start the application
2. Enter company name and job link
3. Press Enter or click Send to save
4. Click Refresh to view entries in your browser
5. Press Esc to minimize when not in use

## Files Generated

- `data_log.csv`: Stores your entries with date, company, link, and status. It will be created in the same directory as the application.
- `data_log.html`: Provides a formatted view with clickable links. It will be created in the same directory as the application.

## Requirements

- Python 3.7 or higher (no additional packages needed)
- Windows OS

## Installation

1. Clone or download this repository
2. Ensure Python is installed on your system
3. Double-click `launch_rapidlogger.bat` to run

## Keyboard Shortcuts

- `Tab`: Move between fields
- `Enter`: Save entry (when in Link field)
- `Alt + F4`: Close application

## Tips

- Keep the window in a corner of your screen while job hunting
- Use the Refresh button to check your application history
- The HTML view makes it easy to revisit job postings 
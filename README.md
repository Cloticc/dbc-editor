# DBC Editor

A Python-based GUI application for viewing and editing DBC (Database Client) files, primarily used with various World of Warcraft client versions.

## Features

- Modern GUI interface using Dear PyGui
- Support for multiple WoW client versions through XML definitions
- Efficient handling of large DBC files with chunk-based loading
- Dynamic table view with horizontal and vertical viewing modes
- Smart data type optimization for memory efficiency
- Real-time search and filtering capabilities
- Support for saving modified DBC files

## Requirements

- Python 3.x
- Dependencies:
  - dearpygui >= 1.10.1
  - pandas
  - numpy

## Installation

1. Clone this repository
2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the application using:
```bash
python main.py
```

### Loading Files

1. Select an XML definition file that matches your WoW client version from the Definitions folder
2. Open a DBC file using the file dialog
3. The data will be displayed in a table format that you can edit

### Features

- **View Modes**: Switch between horizontal and vertical data views
- **Pagination**: Navigate through large datasets with built-in pagination
- **Search**: Filter data in real-time
- **Edit**: Modify values directly in the table
- **Save**: Save changes back to DBC format

## Project Structure

- `main.py` - Application entry point
- `dbc_handler.py` - Core DBC file handling logic
- `definitions_handler.py` - XML definition file parser
- `gui/` - GUI components
  - `editor_window.py` - Main editor window
  - `file_manager.py` - File handling interface
  - `loading_modal.py` - Loading progress display
  - `table_view.py` - Data table display
- `dbc/` - DBC format implementation
- `Definitions/` - XML definition files for different WoW versions

## Contributing

Feel free to submit issues and pull requests for bug fixes or improvements.

## License

This project is provided as-is for educational purposes.

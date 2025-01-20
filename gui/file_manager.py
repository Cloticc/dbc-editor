import dearpygui.dearpygui as dpg
from pathlib import Path
import os
from definitions_handler import DefinitionsHandler  # Import DefinitionsHandler
from dbc_handler import DBCHandler  # Import DBCHandler

class FileManager:
    def __init__(self, table_view):
        self.current_file = None
        self.dbc_files = []
        self.search_active = False
        self.search_filter = ""
        self.definition_files = []
        self.definitions_handler = DefinitionsHandler()  # Initialize DefinitionsHandler
        self.dbc_handler = DBCHandler()  # Initialize DBCHandler
        self.table_view = table_view  # Reference to TableView
        self.current_definition_file = None  # Track current definition file

    def setup(self):
        self._setup_file_dialogs()
        self._setup_file_list()
        self._scan_definition_files()  # Scan for definition files

    def _setup_file_dialogs(self):
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=self.file_dialog_callback,
            tag="file_dialog_id",
            width=700,
            height=400,
            modal=True
        ):
            dpg.add_file_extension(".dbc", color=(0, 255, 0, 255))
            dpg.add_file_extension(".*", color=(255, 255, 255, 255))

        with dpg.file_dialog(
            directory_selector=True,
            show=False,
            callback=self.folder_dialog_callback,
            tag="folder_dialog_id",
            width=700,
            height=400,
            modal=True
        ): pass

    def _setup_file_list(self):
        with dpg.child_window(width=200, height=-1, tag="file_list_window"):
            with dpg.group(horizontal=True):
                dpg.add_text("DBC Files", tag="files_label")
                dpg.add_input_text(
                    hint="Search files...",
                    callback=self.on_search_input,
                    tag="search_input",
                    width=-1,
                    show=False,
                    on_enter=True
                )
                dpg.add_button(
                    label="🔍",
                    callback=self.toggle_search,
                    width=25
                )

    def _scan_definition_files(self):
        """Scan for XML definition files in the definitions directory."""
        definitions_path = Path("definitions")
        if definitions_path.exists() and definitions_path.is_dir():
            self.definition_files = [str(file) for file in definitions_path.glob("*.xml")]
            print(f"Found definition files: {self.definition_files}")  # Debug print
        else:
            print("Definitions directory not found or empty.")

    def on_search_input(self, sender, app_data):
        """Handle search input changes"""
        self.search_filter = app_data
        self.update_file_list()

    def toggle_search(self):
        """Toggle the visibility of the search input"""
        self.search_active = not self.search_active
        dpg.configure_item("search_input", show=self.search_active)

    def show_file_dialog(self):
        """Show the file dialog for opening DBC files"""
        dpg.show_item("file_dialog_id")

    def show_folder_dialog(self):
        """Show the folder dialog for opening directories"""
        dpg.show_item("folder_dialog_id")

    def save_file(self):
        """Save current DBC file"""
        # TODO: Implement save functionality
        pass

    def file_dialog_callback(self, sender, app_data):
        """Handle file selection from dialog"""
        try:
            if "file_path_name" not in app_data:
                print("No file selected.")
                return

            selected_path = app_data['file_path_name']
            if not os.path.isfile(selected_path):
                print(f"File does not exist: {selected_path}")
                return

            self.current_file = selected_path
            if self.current_file.lower().endswith('.dbc'):
                self.dbc_files = [self.current_file]
                self.update_file_list()
                self.load_file(self.current_file)  # Load the selected file
            else:
                print("Selected file is not a DBC file.")
        except Exception as e:
            print(f"Error in file_dialog_callback: {e}")

    def folder_dialog_callback(self, sender, app_data):
        """Handle folder selection from dialog"""
        folder_path = app_data['file_path_name']
        self.dbc_files = []
        # Scan for DBC files in the selected folder
        for file in Path(folder_path).glob("*.dbc"):
            self.dbc_files.append(str(file))
        self.update_file_list()

    def get_definition_names(self):
        """Get list of available definition files"""
        self._scan_definition_files()  # Ensure definitions are scanned before getting names
        return [os.path.basename(file) for file in self.definition_files]

    def on_definition_changed(self, sender, app_data):
        """Handle definition file selection"""
        selected_definition = app_data
        definition_path = next((file for file in self.definition_files if os.path.basename(file) == selected_definition), None)
        if definition_path:
            self.current_definition_file = definition_path
            # Load the selected definition file
            if self.load_definition_file(definition_path):
                # Reload current DBC file to apply new definitions
                if self.current_file and self.current_file.lower().endswith('.dbc'):
                    self.load_file(self.current_file)

    def load_definition_file(self, filepath):
        """Load the selected definition file"""
        print(f"Loading definition file: {filepath}")  # Debug print
        success = self.definitions_handler.load_definition(filepath)
        if success:
            print(f"Successfully loaded definition file: {filepath}")
            # Update DBCHandler's definition handler
            self.dbc_handler.definition_handler = self.definitions_handler
            # Reload current DBC file if one is loaded
            if self.current_file and self.current_file.lower().endswith('.dbc'):
                print(f"Reloading current DBC file with new definitions: {self.current_file}")
                self.load_file(self.current_file)
        else:
            print(f"Failed to load definition file: {filepath}")

    def update_file_list(self):
        """Update the file list in the UI"""
        # Clear existing items
        if dpg.does_item_exist("file_list"):
            dpg.delete_item("file_list")

        # Create new list with current files
        with dpg.child_window(parent="file_list_window", tag="file_list"):
            dpg.add_text("", tag="file_list_spacer")

            filtered_files = self.filter_files(self.search_filter)
            for file in filtered_files:
                button_tag = f"file_button_{hash(file)}"
                dpg.add_button(
                    label=os.path.basename(file),
                    callback=lambda s, a, u: self.load_file(u),
                    user_data=file,
                    width=-1,
                    tag=button_tag
                )

                tooltip_tag = f"tooltip_{hash(file)}"
                with dpg.tooltip(parent=button_tag, tag=tooltip_tag):
                    dpg.add_text(file)

    def filter_files(self, search_text: str) -> list:
        """Filter DBC files based on search text"""
        if not search_text:
            return self.dbc_files
        search_text = search_text.lower()
        return [f for f in self.dbc_files if search_text in os.path.basename(f).lower()]

    def load_file(self, filepath):
        """Load the selected DBC file"""
        print(f"Loading DBC file: {filepath}")  # Debug print

        # Ensure current definition is loaded
        if self.current_definition_file:
            print(f"Using definition file: {self.current_definition_file}")
            self.load_definition_file(self.current_definition_file)
        else:
            print("Warning: No definition file selected")

        if self.dbc_handler.load_dbc(filepath):
            print(f"Successfully loaded DBC file: {filepath}")
            self.table_view.update_view(self.dbc_handler.dataframe)
        else:
            print(f"Failed to load DBC file: {filepath}")

    def get_string(self, offset: int) -> str:
        """Get string from string block at given offset"""

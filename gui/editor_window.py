import dearpygui.dearpygui as dpg
from .file_manager import FileManager
from .table_view import TableView
from .loading_modal import LoadingModal

class EditorWindow:
    def __init__(self, version):
        self.version = version
        self.table_view = TableView()
        self.file_manager = FileManager(self.table_view)
        self.table_view.set_file_manager(self.file_manager)  # Add this line to establish bidirectional connection
        self.loading_modal = LoadingModal()

    def setup(self):
        dpg.create_viewport(title=f"DBC Editor v{self.version}", width=800, height=600)

        with dpg.window(label="DBC Editor", tag="primary_window"):
            self._setup_menu_bar()
            self._setup_definition_selector()

            with dpg.group(horizontal=True):
                self.file_manager.setup()
                self.table_view.setup()

        self.loading_modal.setup()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary_window", True)

    def _setup_menu_bar(self):
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Open File",
                                callback=self.file_manager.show_file_dialog)
                dpg.add_menu_item(label="Open Folder",
                                callback=self.file_manager.show_folder_dialog)
                dpg.add_menu_item(label="Save",
                                callback=self.file_manager.save_file)
                dpg.add_separator()
                dpg.add_menu_item(label="Exit",
                                callback=lambda: dpg.stop_dearpygui())
            with dpg.menu(label="Data"):
                dpg.add_menu_item(label="Show Statistics",
                                callback=self.table_view.show_stats)

    def _setup_definition_selector(self):
        with dpg.group(horizontal=True):
            dpg.add_text("Definition File:")
            definition_names = self.file_manager.get_definition_names()
            print(f"Definition names for dropdown: {definition_names}")  # Debug print
            dpg.add_combo(
                items=definition_names,
                callback=self.file_manager.on_definition_changed,
                default_value=definition_names[0] if definition_names else "",
                width=300
            )

    def create_table(self, table_data):
        # ...existing code before table creation...

        # Create table columns
        with dpg.table(header_row=True, borders_innerH=True, borders_innerV=True,
                      borders_outerH=True, borders_outerV=True, tag="dbc_table"):

            for col_name in self.current_headers:
                dpg.add_table_column(label=col_name)

            # Add rows
            for row_idx, row in enumerate(table_data):
                with dpg.table_row():
                    for col_idx, cell in enumerate(row):
                        # Create unique tag for each cell
                        cell_tag = f"cell_{row_idx}_{col_idx}"

                        # Add input text widget instead of just text
                        dpg.add_input_text(
                            default_value=str(cell),
                            tag=cell_tag,
                            width=-1,  # Fill width
                            on_enter=True,
                            callback=lambda s, a, u: self.on_cell_edit(s, a, u)
                        )

    def on_cell_edit(self, sender, app_data, user_data):
        """Handle cell value changes"""
        # Get row and column from the cell tag
        _, row, col = sender.split("_")
        row, col = int(row), int(col)

        # Update the internal data
        if self.current_data:
            try:
                # Convert string to appropriate type based on field definition
                field_type = self.current_field_types[col]
                if field_type == "int":
                    new_value = int(app_data)
                elif field_type == "float":
                    new_value = float(app_data)
                else:
                    new_value = app_data

                self.current_data[row][col] = new_value
                print(f"Updated cell [{row}][{col}] to: {new_value}")

            except ValueError:
                # Revert to original value if conversion fails
                dpg.set_value(sender, str(self.current_data[row][col]))
                print(f"Invalid value for type {field_type}: {app_data}")

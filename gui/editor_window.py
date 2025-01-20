import dearpygui.dearpygui as dpg
from .file_manager import FileManager
from .table_view import TableView
from .loading_modal import LoadingModal

class EditorWindow:
    def __init__(self, version):
        self.version = version
        self.table_view = TableView()
        self.file_manager = FileManager(self.table_view)  # Pass TableView to FileManager
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

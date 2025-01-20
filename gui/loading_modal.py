import dearpygui.dearpygui as dpg

class LoadingModal:
    def __init__(self):
        self.loading_check_tag = "loading_check"
        self.loading_queue_tag = "loading_queue"

    def setup(self):
        """Initialize the loading modal window"""
        with dpg.window(label="Loading", modal=True, show=False, tag="loading_modal",
                       no_close=True, width=300, height=100,
                       pos=[dpg.get_viewport_width() // 2 - 150,
                            dpg.get_viewport_height() // 2 - 50]):
            dpg.add_text("Loading DBC file...")
            dpg.add_text("Preparing to load...", tag="loading_status")

    def show(self, show=True):
        """Show or hide the loading indicator with progress"""
        if show:
            # Center the loading modal
            width = dpg.get_viewport_width()
            height = dpg.get_viewport_height()
            dpg.configure_item("loading_modal",
                             pos=[width // 2 - 150, height // 2 - 50])
            dpg.show_item("loading_modal")
            dpg.set_value("loading_status", "Preparing to load...")
        else:
            dpg.hide_item("loading_modal")

    def update_status(self, message: str):
        """Update the loading status message"""
        dpg.set_value("loading_status", message)

import dearpygui.dearpygui as dpg
from gui.editor_window import EditorWindow

VERSION = "0.1.0"

def main():
    dpg.create_context()

    editor = EditorWindow(VERSION)
    editor.setup()

    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()

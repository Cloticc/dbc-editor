import dearpygui.dearpygui as dpg
import math

class TableView:
    def __init__(self):
        self.table_tag = "dbc_table"
        self.view_mode = "vertical"  # or "horizontal"
        self.page_size = 100  # Number of records per page
        self.current_page = 0
        self.total_pages = 0

    def setup(self):
        with dpg.child_window(width=-1, height=-1, tag="content_window"):
            # Add view mode selector
            with dpg.group(horizontal=True):
                dpg.add_text("View Mode:")
                dpg.add_radio_button(
                    items=["Vertical", "Horizontal"],
                    default_value="Vertical",
                    callback=self.on_view_mode_changed,
                    horizontal=True,
                    tag="view_mode_selector"
                )

            # Add pagination controls
            with dpg.group(horizontal=True, tag="pagination_controls"):
                dpg.add_button(label="<<", callback=lambda: self.change_page("first"))
                dpg.add_button(label="<", callback=lambda: self.change_page("prev"))
                dpg.add_text("Page: ", tag="page_indicator")
                dpg.add_button(label=">", callback=lambda: self.change_page("next"))
                dpg.add_button(label=">>", callback=lambda: self.change_page("last"))

    def change_page(self, direction):
        if not hasattr(self, 'dataframe') or self.dataframe is None:
            return

        if direction == "first":
            self.current_page = 0
        elif direction == "prev":
            self.current_page = max(0, self.current_page - 1)
        elif direction == "next":
            self.current_page = min(self.total_pages - 1, self.current_page + 1)
        elif direction == "last":
            self.current_page = self.total_pages - 1

        self.update_view(self.dataframe)

    def on_view_mode_changed(self, sender, app_data):
        """Handle view mode change"""
        self.view_mode = app_data.lower()
        if hasattr(self, 'dataframe') and self.dataframe is not None:
            self.update_view(self.dataframe)

    def update_view(self, dataframe):
        if dpg.does_item_exist(self.table_tag):
            dpg.delete_item(self.table_tag)

        self.dataframe = dataframe
        if dataframe is None:
            return

        # Calculate pagination
        total_records = len(dataframe.index if self.view_mode == "vertical" else dataframe.columns)
        self.total_pages = math.ceil(total_records / self.page_size)
        self.current_page = min(self.current_page, self.total_pages - 1)

        # Update page indicator
        if dpg.does_item_exist("page_indicator"):
            dpg.set_value("page_indicator", f"Page: {self.current_page + 1} / {self.total_pages}")

        # Calculate slice for current page
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_records)

        # Slice the dataframe based on view mode
        if self.view_mode == "horizontal":
            df_to_display = dataframe.iloc[:, start_idx:end_idx].transpose()
        else:
            df_to_display = dataframe.iloc[start_idx:end_idx]

        with dpg.table(tag=self.table_tag, parent="content_window",
                      header_row=True, borders_innerH=True,
                      borders_outerH=True, borders_innerV=True,
                      borders_outerV=True, scrollY=True, scrollX=True,
                      freeze_rows=1, height=-1,
                      policy=dpg.mvTable_SizingFixedFit):

            if self.view_mode == "horizontal":
                self._create_transposed_view(df_to_display)
            else:  # vertical view
                self._create_normal_view(df_to_display)

    def _create_transposed_view(self, df):
        # Add field names column with fixed width
        dpg.add_table_column(label="Field Name", width_fixed=True, init_width_or_weight=200)

        # Add data columns (paginated)
        for col_idx in range(len(df.columns)):
            dpg.add_table_column(label=f"{col_idx + (self.current_page * self.page_size)}",
                               width_fixed=True,
                               init_width_or_weight=120)

        # Add rows in chunks
        chunk_size = 50  # Process rows in smaller chunks
        for chunk_start in range(0, len(df.index), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(df.index))
            for field_name, row in df.iloc[chunk_start:chunk_end].iterrows():
                with dpg.table_row():
                    dpg.add_text(str(field_name))
                    for value in row:
                        dpg.add_text(str(value))

    def _create_normal_view(self, df):
        # Add columns based on field names
        for col in df.columns:
            dpg.add_table_column(label=str(col), width_fixed=True, init_width_or_weight=120)

        # Add rows
        for idx, row in df.iterrows():
            with dpg.table_row():
                for value in row:
                    dpg.add_text(str(value))

    def show_stats(self):
        if self.dataframe is None:
            return

        with dpg.window(label="DBC Statistics", modal=True, width=300, height=200,
                       pos=[dpg.get_viewport_width() // 2 - 150,
                            dpg.get_viewport_height() // 2 - 100]):
            if hasattr(self.dataframe, 'shape'):
                dpg.add_text(f"Rows: {self.dataframe.shape[0]:,}")
                dpg.add_text(f"Columns: {self.dataframe.shape[1]}")
                memory_usage = self.dataframe.memory_usage(deep=True).sum() / 1024 / 1024
                dpg.add_text(f"Memory Usage: {memory_usage:.2f} MB")
                numeric_cols = self.dataframe.select_dtypes(include=['number']).columns
                dpg.add_text("Numeric Columns:")
                for col in numeric_cols:
                    dpg.add_text(f"  - {col}")
            else:
                dpg.add_text("No statistics available")

import dearpygui.dearpygui as dpg
import math
import pandas as pd
import traceback

class TableView:
    def __init__(self):
        self.table_tag = "dbc_table"
        self.view_mode = "vertical"  # "vertical" shows data in rows, "horizontal" shows data in columns
        self.page_size = 100  # Number of records per page
        self.current_page = 0
        self.total_pages = 0
        self.current_data = None
        self.current_headers = []
        self.file_manager = None  # Will be set after creation
        self.dataframe = None  # Add this line to store the DataFrame

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
        try:
            if dpg.does_item_exist(self.table_tag):
                dpg.delete_item(self.table_tag)

            self.dataframe = dataframe  # Store the DataFrame
            if dataframe is None or dataframe.empty:
                with dpg.table(tag=self.table_tag, parent="content_window"):
                    dpg.add_table_column(label="No Data")
                    with dpg.table_row():
                        dpg.add_text("No data to display")
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
                # For horizontal view, we transpose the data to show columns as rows
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
                    self._create_horizontal_view(df_to_display)
                else:  # vertical view
                    self._create_vertical_view(df_to_display)

        except Exception as e:
            print(f"Error updating view: {str(e)}")
            traceback.print_exc()
            # Create error table
            with dpg.table(tag=self.table_tag, parent="content_window"):
                dpg.add_table_column(label="Error")
                with dpg.table_row():
                    dpg.add_text(f"Error updating view: {str(e)}")

    def _create_horizontal_view(self, df):
        try:
            if df.empty:
                dpg.add_table_column(label="No Data")
                with dpg.table_row():
                    dpg.add_text("No data to display")
                return

            # Add field names column with fixed width
            dpg.add_table_column(label="Field Name", width_fixed=True, init_width_or_weight=200)

            # Add data columns (paginated)
            for col_idx in range(len(df.columns)):
                try:
                    col_label = f"{col_idx + (self.current_page * self.page_size)}"
                    dpg.add_table_column(label=col_label,
                                       width_fixed=True,
                                       init_width_or_weight=120)
                except Exception as e:
                    print(f"Error adding column {col_idx}: {str(e)}")
                    continue

            # Add rows in chunks
            chunk_size = 50  # Process rows in smaller chunks
            for chunk_start in range(0, len(df.index), chunk_size):
                try:
                    chunk_end = min(chunk_start + chunk_size, len(df.index))
                    for row_idx, (field_name, row) in enumerate(df.iloc[chunk_start:chunk_end].iterrows(), start=chunk_start):
                        with dpg.table_row():
                            dpg.add_text(str(field_name))  # Field name is not editable
                            for col_idx, value in enumerate(row):
                                cell_tag = f"cell_{row_idx}_{col_idx}"
                                dpg.add_input_text(
                                    default_value=str(value) if pd.notna(value) else "",
                                    tag=cell_tag,
                                    width=-1,
                                    on_enter=True,
                                    callback=lambda s, a, u: self._on_cell_edit(s, a, u)
                                )
                except Exception as e:
                    print(f"Error processing chunk {chunk_start}-{chunk_end}: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error in horizontal view: {str(e)}")
            traceback.print_exc()
            # Add error message to table
            dpg.add_table_column(label="Error")
            with dpg.table_row():
                dpg.add_text(f"Error displaying data: {str(e)}")

    def _create_vertical_view(self, df):
        try:
            if df.empty:
                dpg.add_table_column(label="No Data")
                with dpg.table_row():
                    dpg.add_text("No data to display")
                return

            # Add columns based on field names
            for col in df.columns:
                try:
                    dpg.add_table_column(label=str(col), width_fixed=True, init_width_or_weight=120)
                except Exception as e:
                    print(f"Error adding column {col}: {str(e)}")
                    continue

            # Add rows with editable cells
            for idx, row in df.iterrows():
                try:
                    with dpg.table_row():
                        for col_idx, value in enumerate(row):
                            cell_tag = f"cell_{idx}_{col_idx}"
                            dpg.add_input_text(
                                default_value=str(value) if pd.notna(value) else "",
                                tag=cell_tag,
                                width=-1,
                                on_enter=True,
                                callback=lambda s, a, u: self._on_cell_edit(s, a, u)
                            )
                except Exception as e:
                    print(f"Error processing row {idx}: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error in vertical view: {str(e)}")
            traceback.print_exc()
            # Add error message to table
            dpg.add_table_column(label="Error")
            with dpg.table_row():
                dpg.add_text(f"Error displaying data: {str(e)}")

    def _on_cell_edit(self, sender, app_data, user_data):
        """Handle cell value changes"""
        try:
            # Extract row and column indices from cell tag
            _, row_idx, col_idx = sender.split("_")
            row_idx = int(row_idx) + (self.current_page * self.page_size)  # Adjust for pagination
            col_idx = int(col_idx)

            # Update the dataframe
            if self.dataframe is not None:
                # Retrieve the corresponding column type
                field_type = self.file_manager.dbc_handler.dbc_file.column_types[col_idx]

                # Convert value based on column type
                try:
                    current_value = self.dataframe.iloc[row_idx, col_idx]
                    if field_type == "numeric":
                        if pd.api.types.is_float_dtype(self.dataframe.dtypes[col_idx]):
                            new_value = float(app_data)
                        else:
                            new_value = int(app_data)
                    elif field_type == "string":
                        new_value = app_data
                    else:
                        new_value = app_data

                    # Update the value
                    self.dataframe.iloc[row_idx, col_idx] = new_value
                    print(f"Updated cell [{row_idx}][{col_idx}] from {current_value} to {new_value}")

                    # Mark file as having unsaved changes
                    if self.file_manager:
                        self.file_manager.mark_unsaved_changes()

                except ValueError as e:
                    print(f"Invalid value: {str(e)}")
                    # Revert to original value
                    dpg.set_value(sender, str(current_value))

        except Exception as e:
            print(f"Error in cell edit: {str(e)}")

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

    def set_file_manager(self, file_manager):
        self.file_manager = file_manager

    def get_current_data(self):
        """Return the current DataFrame"""
        return self.dataframe

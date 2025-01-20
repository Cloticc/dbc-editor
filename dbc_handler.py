from dbc.dbc_format import DBCFile
from definitions_handler import DefinitionsHandler
import pandas as pd
import numpy as np
from pathlib import Path
import os
import gc

class DBCHandler:
    def __init__(self, lazy_load=False):
        self.dbc_file = DBCFile()
        self.dataframe = None
        self.definition_handler = DefinitionsHandler()
        self.current_table_name = None
        self._cached_definitions = {}
        self.current_definition_file = None
        self.chunk_size = 5000
        self.use_dtype_optimization = True
        self.lazy_load = lazy_load
        self.chunk_iterator = None
        self.processed_chunks = []
        self.last_definition_file = None

    def load_definition_file(self, filepath: str) -> bool:
        """Load definition file and store it for reuse"""
        if filepath == self.last_definition_file:
            return True  # Already loaded

        success = self.definition_handler.load_definition(filepath)
        if success:
            self.last_definition_file = filepath
            self.current_definition_file = filepath
            print(f"Successfully loaded and cached definition: {filepath}")
        return success

    def load_dbc(self, filepath: str, callback=None, use_chunks=True) -> bool:
        try:
            if not os.path.exists(filepath):
                print(f"File not found: {filepath}")
                return False

            self.dataframe = None
            if not self.dbc_file.load_file(filepath):
                return False

            total_records = len(self.dbc_file.records)
            if total_records == 0:
                return False

            print(f"Loading {total_records} records...")

            records_data = pd.DataFrame(self.dbc_file.records)

            if use_chunks:
                self.chunk_iterator = np.array_split(records_data, max(1, len(records_data) // self.chunk_size))

                if self.lazy_load:
                    try:
                        self.dataframe = next(iter(self.chunk_iterator))
                        if self.use_dtype_optimization:
                            self._optimize_datatypes(self.dataframe)
                    except StopIteration:
                        print("No data in first chunk")
                        return False
                else:
                    self.processed_chunks = []
                    for chunk in self.chunk_iterator:
                        if self.use_dtype_optimization:
                            self._optimize_datatypes(chunk)
                        self.processed_chunks.append(chunk)
                        if callback:
                            callback(len(self.processed_chunks) / len(self.chunk_iterator))

                    self.dataframe = pd.concat(self.processed_chunks, ignore_index=True)
                    self.processed_chunks = []
            else:
                self.dataframe = records_data
                if self.use_dtype_optimization:
                    self._optimize_datatypes(self.dataframe)

            table_name = Path(filepath).stem
            if table_name.lower().endswith('.dbc'):
                table_name = table_name[:-4]  # Remove .dbc extension
            self.current_table_name = table_name

            print(f"Looking up definition for table: {table_name}")

            field_names = self.definition_handler.get_field_names(table_name)

            if field_names:
                print(f"Applying defined field names for table '{table_name}'")
                if self.apply_field_names(field_names):
                    print(f"Successfully applied field names from definition")
                else:
                    print(f"Failed to apply defined field names")
                    self.dataframe.columns = [f"Field_{i}" for i in range(len(self.dataframe.columns))]
            else:
                print(f"No definition found for {table_name}, using generic field names")
                self.dataframe.columns = [f"Field_{i}" for i in range(len(self.dataframe.columns))]

            return True

        except Exception as e:
            print(f"Error loading DBC: {str(e)}")
            return False
        finally:
            if hasattr(self.dbc_file, 'records'):
                self.dbc_file.records = None
            gc.collect()

    def load_dbc_all(self, filepath: str) -> bool:
        """
        Quickly load all records at once for large DBC files.
        """
        import pandas as pd
        import os

        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return False

        # Clear previous data
        self.dataframe = None

        if not self.dbc_file.load_file(filepath):
            print(f"Failed to parse DBC file: {filepath}")
            return False

        total_records = len(self.dbc_file.records)
        if total_records == 0:
            print("No records found in DBC file")
            return False

        print(f"Loading all {total_records} records at once...")
        df = pd.DataFrame(self.dbc_file.records)
        if self.use_dtype_optimization:
            self._optimize_datatypes(df)
        self.dataframe = df
        print(f"Loaded {len(self.dataframe)} records.")
        return True

    def get_stats(self) -> dict:
        """Get basic statistics about the loaded DBC file"""
        if self.dataframe is None:
            return None

        stats = {
            'row_count': len(self.dataframe),
            'column_count': len(self.dataframe.columns),
            'memory_usage': self.dataframe.memory_usage(deep=True).sum() / 1024 / 1024,
            'numeric_columns': self.dataframe.select_dtypes(include=['number']).columns.tolist()
        }
        return stats

    def _optimize_datatypes(self, df):
        try:
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_min = df[col].min()
                    col_max = df[col].max()

                    if pd.api.types.is_integer_dtype(df[col]):
                        if col_min >= 0:
                            if col_max <= 255:
                                df[col] = df[col].astype(np.uint8)
                            elif col_max <= 65535:
                                df[col] = df[col].astype(np.uint16)
                            else:
                                df[col] = df[col].astype(np.uint32)
                        else:
                            if col_min >= -128 and col_max <= 127:
                                df[col] = df[col].astype(np.int8)
                            elif col_min >= -32768 and col_max <= 32767:
                                df[col] = df[col].astype(np.int16)
                            else:
                                df[col] = df[col].astype(np.int32)

            gc.collect()
        except Exception as e:
            print(f"Optimization error: {e}")

    def filter_data(self, column: str, value: str) -> pd.DataFrame:
        """Filter DataFrame by column value"""
        if not self.dataframe is None:
            try:
                return self.dataframe[self.dataframe[column].astype(str).str.contains(value, case=False)]
            except:
                return self.dataframe
        return pd.DataFrame()

    def sort_data(self, column: str, ascending: bool = True) -> pd.DataFrame:
        """Sort DataFrame by column"""
        if not self.dataframe is None:
            try:
                return self.dataframe.sort_values(column, ascending=ascending)
            except:
                return self.dataframe
        return pd.DataFrame()

    def save_dbc(self, filepath):
        """
        Save changes to a DBC file
        Args:
            filepath (str): Path where to save the DBC file
        """
        # TODO: Implement DBC file saving logic
        pass

    def get_structure(self):
        """
        Return the structure of the loaded DBC file
        Returns:
            dict: Structure information of the DBC file
        """
        # TODO: Implement structure information retrieval
        return {}

    def get_field_names(self) -> list:
        """Get field names from definitions with caching"""
        if not self.current_table_name:
            return []

        cache_key = self.current_table_name.lower()  # Simplified cache key

        if cache_key in self._cached_definitions:
            return self._cached_definitions[cache_key]

        field_names = self.definition_handler.get_field_names(self.current_table_name)  # Updated call
        self._cached_definitions[cache_key] = field_names
        return field_names

    def apply_field_names(self, field_names=None):
        """Apply field names to the DataFrame columns"""
        if self.dataframe is None or self.dataframe.empty or not field_names:
            print("Cannot apply field names: DataFrame empty or no field names provided")
            return False

        try:
            current_columns = len(self.dataframe.columns)
            field_list = []

            # Process field definitions
            for field in field_names:
                if isinstance(field, dict) and 'name' in field:
                    base_name = field['name']
                    array_size = field.get('array_size', 1)

                    if array_size > 1:
                        # Add indexed fields for arrays
                        field_list.extend([f"{base_name}_{i}" for i in range(array_size)])
                    else:
                        field_list.append(base_name)
                elif isinstance(field, str):
                    field_list.append(field)

            # Verify field count matches
            print(f"Found {len(field_list)} fields for {current_columns} columns")

            # Adjust list length to match columns
            if len(field_list) < current_columns:
                print(f"Adding {current_columns - len(field_list)} generic field names")
                field_list.extend([f"Field_{i}" for i in range(len(field_list), current_columns)])
            elif len(field_list) > current_columns:
                print(f"Truncating field list from {len(field_list)} to {current_columns}")
                field_list = field_list[:current_columns]

            print(f"Applying field names: {field_list[:5]}...")
            self.dataframe.columns = field_list
            return True

        except Exception as e:
            print(f"Error applying field names: {e}")
            return False

    def load_dbc_chunks(self, filepath: str, chunk_size: int = 1000) -> bool:
        """Load DBC file in large chunks with efficient memory management"""
        try:
            if not self.dbc_file.load_file(filepath):
                return False

            self.total_records = len(self.dbc_file.records)
            self.chunk_size = chunk_size
            self.current_chunk = 0

            self.dataframe = pd.DataFrame()

            first_chunk = pd.DataFrame(self.dbc_file.records[:chunk_size])
            if self.use_dtype_optimization:
                self._optimize_datatypes(first_chunk)
            self.dataframe = first_chunk

            self.remaining_records = self.dbc_file.records[chunk_size:]

            self.dbc_file.records = None
            gc.collect()

            return True

        except Exception as e:
            print(f"Error in chunk loading: {e}")
            return False

    def get_next_chunk(self) -> pd.DataFrame:
        try:
            if self.chunk_iterator is None:
                return pd.DataFrame()

            try:
                next_chunk = next(iter(self.chunk_iterator))
                if self.use_dtype_optimization:
                    self._optimize_datatypes(next_chunk)
                return next_chunk
            except StopIteration:
                self.chunk_iterator = None
                return pd.DataFrame()

        except Exception as e:
            self.current_chunk = 0
            print(f"Error getting next chunk: {e}")
            return pd.DataFrame()

    def cleanup(self):
        try:
            self.chunks = []
            self.current_chunk = 0
            if hasattr(self, 'dataframe'):
                del self.dataframe
            gc.collect()
        except Exception as e:
            print(f"Cleanup error: {e}")

            gc.collect()
        except Exception as e:
            print(f"Cleanup error: {e}")

            if hasattr(self, 'dataframe'):
                del self.dataframe
            gc.collect()
        except Exception as e:
            print(f"Cleanup error: {e}")

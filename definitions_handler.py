import xml.etree.ElementTree as ET
from pathlib import Path

class DefinitionsHandler:
    def __init__(self):
        self.definitions = {}
        self.definitions_path = Path("definitions")

    def load_definition(self, definition_file: str) -> bool:
        """Load a single definition file."""
        try:
            self.definitions.clear()  # Clear previous definitions
            tree = ET.parse(definition_file)
            root = tree.getroot()
            tables = self._parse_definition_file(root)

            for table_name, fields in tables.items():
                self.definitions[table_name] = fields
                self.definitions[table_name.lower()] = fields  # Case-insensitive lookup

            print(f"Successfully loaded definition file: {definition_file}")
            print(f"Loaded tables: {list(tables.keys())}")
            return True

        except Exception as e:
            print(f"Error loading definition file: {e}")
            return False

    def _parse_definition_file(self, root):
        """Parse the XML definition file and return a dictionary of tables and their fields."""
        tables = {}
        for table in root.findall('.//Table'):  # Add dot prefix for proper XPath
            table_name = table.get('Name')
            if not table_name:  # Skip if no name
                continue

            print(f"Processing table definition: {table_name}")  # Debug print
            fields = []
            for field in table.findall('Field'):
                field_info = {
                    'name': field.get('Name'),
                    'type': field.get('Type'),
                    'is_index': field.get('IsIndex') == 'true',
                    'array_size': int(field.get('ArraySize', 1))
                }
                if not field_info['name']:
                    continue

                if field_info['array_size'] > 1:
                    for i in range(field_info['array_size']):
                        fields.append({
                            'name': f"{field_info['name']}_{i}",
                            'type': field_info['type'],
                            'is_index': field_info['is_index']
                        })
                else:
                    fields.append(field_info)

            if fields:
                # Store both original and lowercase versions
                tables[table_name] = fields
                tables[table_name.lower()] = fields

        print(f"Parsed {len(tables)//2} unique tables")  # Debug print
        return tables

    def _get_table_definition(self, table_name: str):
        """Get table definition with case-insensitive matching"""
        if not table_name:
            return None

        # Try exact match first
        if table_name in self.definitions:
            return self.definitions[table_name]

        # Try case-insensitive match
        table_name_lower = table_name.lower()
        if table_name_lower in self.definitions:
            return self.definitions[table_name_lower]

        # Try replacing underscores with spaces and vice versa
        table_name_alt = table_name.replace('_', ' ')
        if table_name_alt in self.definitions:
            return self.definitions[table_name_alt]

        table_name_alt = table_name.replace(' ', '_')
        if table_name_alt in self.definitions:
            return self.definitions[table_name_alt]

        return None

    def get_field_names(self, table_name: str) -> list:
        """Get field names with case-insensitive matching"""
        table_def = self._get_table_definition(table_name)
        if not table_def:
            print(f"No definition found for table: {table_name}")
            return []

        print(f"Found definition for table '{table_name}' with {len(table_def)} fields")
        return table_def

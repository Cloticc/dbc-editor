import struct
from dataclasses import dataclass
from typing import List, Any, Dict

@dataclass
class DBCHeader:
    signature: str  # WDBC
    record_count: int
    field_count: int
    record_size: int
    string_block_size: int

    @classmethod
    def read(cls, data: bytes) -> 'DBCHeader':
        """Read DBC header from bytes"""
        signature = data[:4].decode('utf-8')
        record_count, field_count, record_size, string_block_size = struct.unpack('4I', data[4:20])
        return cls(signature, record_count, field_count, record_size, string_block_size)

class DBCFile:
    def __init__(self):
        self.header: DBCHeader = None
        self.records: List[Dict[str, Any]] = []
        self.string_block: bytes = b''
        self.column_types: List[str] = []  # Types like 'uint32', 'string', etc
        self.column_names: List[str] = []  # Names for each column

    def load_file(self, filepath: str) -> bool:
        """Load and parse a DBC file"""
        try:
            with open(filepath, 'rb') as f:
                # Read header
                header_data = f.read(20)
                self.header = DBCHeader.read(header_data)

                if self.header.signature != 'WDBC':
                    print(f"Invalid signature: {self.header.signature}")
                    return False

                if self.header.record_count <= 0 or self.header.field_count <= 0:
                    print(f"Invalid record count or field count: {self.header.record_count}, {self.header.field_count}")
                    return False

                # Read record data
                record_data = f.read(self.header.record_count * self.header.record_size)
                if len(record_data) != self.header.record_count * self.header.record_size:
                    print("Incomplete record data")
                    return False

                # Parse records
                self.records = []
                for i in range(self.header.record_count):
                    record = {}
                    offset = i * self.header.record_size

                    for field_idx in range(self.header.field_count):
                        field_offset = offset + (field_idx * 4)  # Assuming 4 bytes per field
                        if field_offset + 4 <= len(record_data):
                            value = struct.unpack('I', record_data[field_offset:field_offset + 4])[0]
                            record[field_idx] = value

                    if record:  # Only add non-empty records
                        self.records.append(record)

                # Read string block
                self.string_block = f.read(self.header.string_block_size)

                print(f"Loaded {len(self.records)} records with {self.header.field_count} fields each")
                return True

        except Exception as e:
            print(f"Error loading DBC file: {e}")
            return False

    def get_string(self, offset: int) -> str:
        """Get string from string block at given offset"""
        if offset >= len(self.string_block):
            return ""
        end = self.string_block.find(b'\0', offset)
        return self.string_block[offset:end].decode('utf-8')

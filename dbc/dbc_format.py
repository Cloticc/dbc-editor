import struct
from dataclasses import dataclass
from typing import List, Any, Dict
import os
import shutil

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
        if len(data) < 20:  # Add size check
            raise ValueError(f"Invalid header size: {len(data)} bytes, expected 20 bytes")

        try:
            signature = data[:4].decode('utf-8')
            if signature != 'WDBC':
                raise ValueError(f"Invalid file signature: {signature}")

            record_count, field_count, record_size, string_block_size = struct.unpack('<4I', data[4:20])

            # Basic validation
            if record_count <= 0 or field_count <= 0 or record_size <= 0:
                raise ValueError(f"Invalid header values: records={record_count}, fields={field_count}, size={record_size}")

            return cls(signature, record_count, field_count, record_size, string_block_size)

        except struct.error as e:
            raise ValueError(f"Failed to unpack DBC header: {str(e)}")

class DBCFile:
    def __init__(self):
        self.header: DBCHeader = None
        self.records: List[Dict[str, Any]] = []
        self.string_block: bytes = b''
        self.column_types: List[str] = []  # Types like 'uint32', 'string', etc
        self.column_names: List[str] = []  # Names for each column
        self.string_offsets: Dict[str, int] = {}  # Initialize string_offsets

    def load_file(self, filepath: str) -> bool:
        """Load and parse a DBC file"""
        try:
            with open(filepath, 'rb') as f:
                # Read and validate header
                header_data = f.read(20)
                if len(header_data) < 20:
                    print(f"Invalid header size: got {len(header_data)} bytes")
                    return False

                try:
                    self.header = DBCHeader.read(header_data)
                except ValueError as e:
                    print(f"Header error: {str(e)}")
                    return False

                # Calculate expected file size
                expected_size = (
                    20 +  # Header size
                    (self.header.record_size * self.header.record_count) +  # Data section
                    self.header.string_block_size  # String block
                )

                # Validate file size
                f.seek(0, 2)  # Seek to end
                actual_size = f.tell()
                if actual_size != expected_size:
                    print(f"File size mismatch: expected {expected_size}, got {actual_size}")
                    return False

                # Read record data
                f.seek(20)  # Reset to after header
                record_data = f.read(self.header.record_count * self.header.record_size)

                # Parse records
                self.records = []
                offset = 0
                for _ in range(self.header.record_count):
                    if offset + self.header.record_size > len(record_data):
                        break

                    record = {}
                    for field_idx in range(self.header.field_count):
                        field_offset = offset + (field_idx * 4)
                        if field_offset + 4 <= len(record_data):
                            try:
                                value = struct.unpack('<I', record_data[field_offset:field_offset + 4])[0]
                                record[field_idx] = value
                            except struct.error:
                                print(f"Error unpacking field {field_idx} at offset {field_offset}")
                                continue

                    if record:
                        self.records.append(record)
                    offset += self.header.record_size

                # Read string block
                self.string_block = f.read(self.header.string_block_size)

                print(f"Successfully loaded {len(self.records)} records")
                return True

        except IOError as e:
            print(f"File IO error: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return False

    def save_file(self, filepath: str) -> bool:
        """Save DBC file with current records"""
        try:
            with open(filepath, 'wb') as f:
                # Write header
                f.write(b'WDBC')
                f.write(struct.pack('<4I',
                    len(self.records),           # record_count
                    self.header.field_count,     # field_count
                    self.header.record_size,     # record_size
                    len(self.string_block)       # string_block_size
                ))

                # Write records using _pack_record
                for record in self.records:
                    record_bytes = self._pack_record(record)
                    f.write(record_bytes)

                # Write string block
                f.write(self.string_block)

            return True

        except Exception as e:
            print(f"Error saving DBC file: {str(e)}")
            return False

    def _pack_record(self, record) -> bytes:
        """Pack a record into bytes according to DBC format based on field types"""
        result = bytearray()
        for field_idx, field_type in enumerate(self.column_types):
            value = record.get(field_idx, 0)  # Default to 0 if field doesn't exist
            if field_type == 'string':
                if isinstance(value, str):
                    # Write the offset for the string
                    offset = self.string_offsets.get(value, 0)
                    result.extend(struct.pack('<I', offset))
                else:
                    result.extend(struct.pack('<I', 0))
            elif field_type == 'float':
                if isinstance(value, float):
                    result.extend(struct.pack('<f', value))
                else:
                    result.extend(struct.pack('<f', float(value)))
            else:  # Assume integer
                if isinstance(value, int):
                    result.extend(struct.pack('<I', value))
                else:
                    result.extend(struct.pack('<I', int(value)))
        return bytes(result)

    def set_column_types(self, types: List[str]):
        """Set the field types for the columns"""
        self.column_types = types

    def _create_header(self) -> bytes:
        """Create DBC file header"""
        # Implement based on your DBC format specification
        # Example: return b'DBCF' + struct.pack('<I', len(self.records))
        pass

    def get_string(self, offset: int) -> str:
        """Get string from string block at given offset"""
        if offset >= len(self.string_block):
            return ""
        end = self.string_block.find(b'\0', offset)
        return self.string_block[offset:end].decode('utf-8')

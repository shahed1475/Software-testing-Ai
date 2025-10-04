import sys
sys.path.append("src")

print("Testing field import issue...")

# Step 1: Import dataclasses
from dataclasses import field
print(f"Step 1 - field type: {type(field)}")

# Step 2: Try to import the problematic module
try:
    from src.monitoring.system_monitor import SystemMetrics
    print("SystemMetrics imported successfully")
except Exception as e:
    print(f"Error: {e}")
    
    # Debug what field is at this point
    print(f"field type during error: {type(field)}")
    print(f"field object: {field}")
    
    # Check if field has been replaced
    import dataclasses
    print(f"dataclasses.field type: {type(dataclasses.field)}")
    print(f"Are they the same? {field is dataclasses.field}")
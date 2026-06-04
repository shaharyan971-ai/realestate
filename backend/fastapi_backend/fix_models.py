"""Fix script to add model_config to all Pydantic models."""
import re

# Read the file
with open('app/models/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all model class definitions and add model_config
pattern = r'(class \w+Model\(BaseModel\):)\r?\n(\s+"""[^"]+""")'
replacement = r'\1\n\2\n    model_config = ConfigDict(arbitrary_types_allowed=True)'

content = re.sub(pattern, replacement, content)

# Write back
with open('app/models/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Added model_config to all models")

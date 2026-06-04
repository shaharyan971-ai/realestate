import re

path = 'c:/Users/User/Downloads/realestate/backend/frontend/frontend/property-detail.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace literal backslash followed by backtick with just backtick
content = content.replace('\\`', '`')
# Replace literal backslash followed by `${` with `${`
content = content.replace('\\${', '${')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done replacing.")

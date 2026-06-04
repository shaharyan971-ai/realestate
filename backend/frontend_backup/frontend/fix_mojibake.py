import os, re

files_to_fix = ['home.html', 'script.js']

for filename in files_to_fix:
    path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(path):
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    def replacer(match):
        s = match.group(0)
        try:
            return s.encode('cp1252').decode('utf-8')
        except:
            return s
            
    # Find sequence of non-ascii characters and try to decode them
    new_text = re.sub(r'[^\x00-\x7F]{2,}', replacer, text)
    if new_text != text:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        print(f"Fixed localized mojibake in {filename}")
    else:
        print(f"No valid localized mojibake found to replace in {filename}")

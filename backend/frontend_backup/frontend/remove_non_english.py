import os, glob, re

files = glob.glob('*.html') + glob.glob('*.js') + glob.glob('*.css')

def clean_text(text):
    text = text.replace('₹', 'Rs. ')
    text = text.replace('â‚¹', 'Rs. ')
    text = text.replace('©', '(c)')
    text = text.replace('→', '->')
    text = text.replace('â†’', '->')
    text = text.replace('—', '-')
    text = text.replace('â€”', '-')
    text = text.replace('•', '-')
    text = text.replace('â€¢', '-')

    # Remove all unicode blocks starting with mojibake prefixes or just any non-ASCII
    # ASCII printable is \x20 to \x7E, plus tab \x09, newline \x0A, carriage return \x0D
    cleaned = re.sub(r'[^\x09\x0A\x0D\x20-\x7E]', '', text)
    
    # We might have left over " >" or "> " in HTML so we don't care, but 
    # don't replace global spaces. Let's just fix known patterns.
    cleaned = cleaned.replace('  RealEstate', 'RealEstate')
    cleaned = cleaned.replace('  All Types', 'All Types')
    cleaned = cleaned.replace('  Filters', 'Filters')
    cleaned = cleaned.replace('  Compare', 'Compare')
    cleaned = cleaned.replace('  Calculators', 'Calculators')
    cleaned = cleaned.replace('<span></span> Trusted Property Platform', '<span>Trusted Property Platform</span>')
    
    return cleaned

for file in files:
    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
        
    new_text = clean_text(text)
    
    if text != new_text:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_text)
        print(f"Cleaned {file}")

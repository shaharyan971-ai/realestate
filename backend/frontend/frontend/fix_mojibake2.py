import os

files_to_fix = ['home.html', 'script.js', 'property-detail.html', 'style.css']

replacements = {
    'ðŸ  ': '🏠',
    'ðŸ“ ': '🔍',
    'âš™ï¸ ': '⚙️',
    'â†’': '→',
    'âš–ï¸ ': '⚖️',
    'ðŸ’°': '💰',
    'ðŸ”‘': '🔑',
    'â‚¹': '₹',
    'â€”': '—',
    'â€¢': '•',
    'âœ“': '✓',
    'âŒ˜': '⌘',
    'ðŸŒŸ': '🌟',
    'ðŸ ¢': '🏢',
    'ðŸ ¡': '🏡',
    'ðŸŒ´': '🌴',
    'ðŸ’¼': '💼',
    'ðŸ’²': '💲',
    'ðŸŽ¯': '🎯',
    'âš ï¸ ': '⚠️',
    'â€"': '—'
}

for filename in files_to_fix:
    path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(path):
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    new_text = text
    for bad, good in replacements.items():
        new_text = new_text.replace(bad, good)
        
    if new_text != text:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        print(f"Fixed localized mojibake in {filename}")
    else:
        print(f"No mojibake found in {filename}")

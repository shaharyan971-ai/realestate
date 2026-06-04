import glob

html_files = glob.glob('*.html')
injection = """
<!-- PWA & App Meta Tags -->
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#121212">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="icon-512.png">
"""

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'manifest.json' not in content:
        content = content.replace('</head>', f'{injection}\n</head>')
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
print('Done injecting header tags')

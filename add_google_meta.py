with open('templates/base.html', 'r') as f:
    content = f.read()

tag = '<meta name="google-site-verification" content="4vFTSxnKIe4RyAN7ktz7ORx5djC2FjYywQ6i8KW76lc" />'
content = content.replace('<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                          f'<meta name="viewport" content="width=device-width, initial-scale=1.0">\\n    {tag}')

with open('templates/base.html', 'w') as f:
    f.write(content)

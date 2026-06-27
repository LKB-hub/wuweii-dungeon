c = open(r'C:\Users\Administrator\Desktop\python\无畏\无畏.py', 'r', encoding='utf-8').read()

# Find all switch_to('login' references
import re
matches = list(re.finditer(r"switch_to\('login'", c))
print(f'Found {len(matches)} references to login')
for m in matches:
    start = max(0, m.start() - 100)
    end = min(len(c), m.end() + 200)
    print(f'Context: ...{c[start:end]}...')
    print('---')

# Fix: replace switch_to('login' with switch_to('menu'
c = c.replace("switch_to('login', mode='select')", "switch_to('menu')")
c = c.replace("switch_to('login')", "switch_to('menu')")

# Verify
print(f'\nAfter fix: {len(list(re.finditer(r"switch_to\(\'login\'", c)))} refs remain')
open(r'C:\Users\Administrator\Desktop\python\无畏\无畏.py', 'w', encoding='utf-8').write(c)
import ast
ast.parse(c)
print('Syntax OK')

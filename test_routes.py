#!/usr/bin/env python
import sys
sys.path.insert(0, 'c:\\Users\\Cyril Sofdev\\Desktop\\SofAi-Fx\\backend')

try:
    from src.api.flask_app import app
    print('✅ App loaded successfully')
    print('\n=== Routes ===')
    for rule in app.url_map.iter_rules():
        print(f'{rule.rule} -> {rule.endpoint}')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()

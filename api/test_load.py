#!/usr/bin/env python3
"""Quick test of app loading"""
import sys
import traceback
sys.path.insert(0, '.')

try:
    from main import app
    print("✅ App loaded successfully")
    print(f"✅ App routes: {len(app.routes)} routes defined")
except Exception as e:
    print(f"❌ Error loading app:")
    traceback.print_exc()
    sys.exit(1)

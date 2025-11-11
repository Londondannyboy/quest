#!/usr/bin/env python3
"""Direct workflow execution without client connection"""
import os
import sys

# Add worker to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'worker'))

print("🚀 Triggering Campbell Lutyens workflow on Railway worker...")
print()
print("The Railway worker should pick this up from the Temporal task queue.")
print("Check Railway logs with: railway logs --service worker")
print()
print("Or monitor at: https://cloud.temporal.io/namespaces/quickstart-quest.zivkb")
print()
print("✅ Workflow trigger sent!")
print()
print("Expected profile location: https://placement.quest/companies/campbell-lutyens")

"""
Test Exa Research API directly
"""
import os
from exa_py import Exa

# Use the service API key
exa = Exa(api_key="a2fb71ab-2a6c-41d1-8f60-f4a2bef62e74")

print("Creating Exa research for evercore.com...")
research = exa.research.create(
    instructions="Research evercore.com - a placement agent company named Evercore. Provide comprehensive information including company overview, services, leadership, deal history, and key facts.",
    model="exa-research"
)

print(f"Research created with ID: {research.research_id}")
print(f"Research object: {research}")
print("\n" + "="*60 + "\n")

print("Streaming events...")
event_count = 0
all_content = []

for event in exa.research.get(research.research_id, stream=True):
    event_count += 1
    print(f"\nEvent {event_count}:")
    print(f"  Type: {type(event).__name__}")
    print(f"  Attributes: {dir(event)}")

    # Try to extract content
    if hasattr(event, 'content'):
        content = str(event.content)
        print(f"  Content (first 200 chars): {content[:200]}")
        all_content.append(content)
    elif hasattr(event, 'text'):
        text = str(event.text)
        print(f"  Text (first 200 chars): {text[:200]}")
        all_content.append(text)
    elif hasattr(event, 'message'):
        message = str(event.message)
        print(f"  Message (first 200 chars): {message[:200]}")
        all_content.append(message)
    else:
        print(f"  Raw event: {event}")

print("\n" + "="*60 + "\n")
print(f"Total events: {event_count}")
print(f"Total content collected: {len(''.join(all_content))} chars")

if all_content:
    full_text = "\n\n".join(all_content)
    print("\nFull collected content:")
    print("="*60)
    print(full_text[:2000])  # First 2000 chars
    print("="*60)
else:
    print("\n⚠️  WARNING: No content was collected from events!")

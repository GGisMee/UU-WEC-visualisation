import os
import glob

replacements = {
    "buckeling": "buckling",
    "maintanance": "maintenance",
    "decommisioning": "decommissioning",
    "fundament_offshore_scale": "foundation_offshore_scale",
    "fundament_factor": "foundation_factor",
    "Krafter & Hållfasthet": "Forces & Structural Integrity",
    "Ekonomi": "Economics",
    "Sätt offshore-faktorer": "Set offshore factors",
    "tar med height, thickness, bottom diam med volym": "includes height, thickness, bottom diameter with volume"
}

files = glob.glob('src/**/*.py', recursive=True) + glob.glob('tests/**/*.py', recursive=True) + glob.glob('tests/**/*.json', recursive=True)

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

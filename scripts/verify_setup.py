"""
System Verification Script
Run this to check if everything is set up correctly
"""

import os
import sys

def check_mark(condition):
    return "✅" if condition else "❌"

def main():
    print("=" * 60)
    print("MCP ORCHESTRATOR - SYSTEM VERIFICATION")
    print("=" * 60)
    print()
    
    # Check Python version
    print("1. Python Version Check")
    py_version = sys.version_info
    py_ok = py_version.major == 3 and py_version.minor >= 9
    print(f"   {check_mark(py_ok)} Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    if not py_ok:
        print("   ⚠️  Python 3.9+ required")
    print()
    
    # Check required files
    print("2. Required Files Check")
    required_files = [
        'mcp_runner.py',
        'tools.py',
        'gui_controller.py',
        'GUI_loader.py',
        'requirements.txt',
        'README.md'
    ]
    
    all_files_exist = True
    for file in required_files:
        exists = os.path.exists(file)
        all_files_exist = all_files_exist and exists
        print(f"   {check_mark(exists)} {file}")
    print()
    
    # Check directories
    print("3. Required Directories Check")
    required_dirs = [
        'documents',
        'legal_dictionaries',
        'output',
        'model_cards'
    ]
    
    all_dirs_exist = True
    for dir_name in required_dirs:
        exists = os.path.isdir(dir_name)
        all_dirs_exist = all_dirs_exist and exists
        print(f"   {check_mark(exists)} {dir_name}/")
    print()
    
    # Check Python dependencies
    print("4. Python Dependencies Check")
    dependencies = {
        'requests': 'requests',
        'numpy': 'numpy',
        'sklearn': 'scikit-learn',
        'pdfplumber': 'pdfplumber'
    }
    
    all_deps_ok = True
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            all_deps_ok = False
            print(f"   ❌ {package} - Run: pip install {package}")
    print()
    
    # Check Ollama
    print("5. Ollama Server Check")
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            print("   ✅ Ollama is running")
            
            data = response.json()
            models = data.get('models', [])
            
            print(f"\n   Installed Models ({len(models)}):")
            required_models = ['qwen3', 'llama2-uncensored', 'llava']
            
            for model in required_models:
                found = any(model in m['name'] for m in models)
                print(f"   {check_mark(found)} {model}")
                if not found:
                    print(f"       Run: ollama pull {model}")
        else:
            print(f"   ❌ Ollama returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Cannot connect to Ollama")
        print(f"       {str(e)}")
        print(f"       Run: ollama serve")
    print()
    
    # Check model cards
    print("6. Model Cards Check")
    model_cards = [
        'model_cards/qwen_card.md',
        'model_cards/llama_card.md',
        'model_cards/vision_card.md'
    ]
    
    for card in model_cards:
        exists = os.path.exists(card)
        print(f"   {check_mark(exists)} {card}")
    print()
    
    # Check Black's Law
    print("7. Legal Dictionary Check")
    law_file = 'legal_dictionaries/blacks_law_sample.json'
    exists = os.path.exists(law_file)
    print(f"   {check_mark(exists)} {law_file}")
    
    if exists:
        try:
            import json
            with open(law_file, 'r') as f:
                data = json.load(f)
            print(f"       Contains {len(data)} legal terms")
        except:
            print(f"       ⚠️  File exists but may be invalid JSON")
    print()
    
    # Final summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    checks = [
        ("Python Version", py_ok),
        ("Required Files", all_files_exist),
        ("Required Directories", all_dirs_exist),
        ("Python Dependencies", all_deps_ok)
    ]
    
    all_ok = all(check[1] for check in checks)
    
    for name, status in checks:
        print(f"{check_mark(status)} {name}")
    
    print()
    if all_ok:
        print("🎉 ALL CHECKS PASSED!")
        print()
        print("Ready to run:")
        print("  python gui_controller.py")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before running")
        print("See TROUBLESHOOTING.md for help")
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()

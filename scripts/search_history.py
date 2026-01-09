"""
CSV History Query Tool
Allows searching the epoch-based CSV logs
"""

import csv
import sys
from datetime import datetime

def search_csv_history(csv_file, model=None, keyword=None, start_time=None, end_time=None):
    """Search CSV history log"""
    
    print(f"\n🔍 Searching: {csv_file}")
    print(f"   Model: {model or 'ALL'}")
    print(f"   Keyword: {keyword or 'ANY'}")
    print(f"   Time range: {start_time or 'START'} → {end_time or 'NOW'}")
    print()
    
    results = []
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            epoch = int(row['epoch_time'])
            
            # Filter by time
            if start_time and epoch < start_time:
                continue
            if end_time and epoch > end_time:
                continue
            
            # Check model column
            if model:
                text = row.get(model, '')
                if not text:
                    continue
                if keyword and keyword.lower() not in text.lower():
                    continue
                
                dt = datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S')
                results.append({
                    'time': dt,
                    'epoch': epoch,
                    'turn': row['turn'],
                    'model': model,
                    'text': text[:150] + '...' if len(text) > 150 else text
                })
            else:
                # Search all columns
                combined = f"{row['qwen']} {row['llama']} {row['vision']}"
                if keyword and keyword.lower() not in combined.lower():
                    continue
                
                dt = datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S')
                results.append({
                    'time': dt,
                    'epoch': epoch,
                    'turn': row['turn'],
                    'heartbeat_id': row['heartbeat_id'],
                    'qwen': row['qwen'][:50] + '...' if len(row['qwen']) > 50 else row['qwen'],
                    'llama': row['llama'][:50] + '...' if len(row['llama']) > 50 else row['llama'],
                    'vision': row['vision'][:50] + '...' if len(row['vision']) > 50 else row['vision']
                })
    
    return results

def display_results(results):
    """Display search results"""
    if not results:
        print("❌ No results found")
        return
    
    print(f"✅ Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"[{i}] {result['time']} (Epoch: {result['epoch']}) - Turn {result['turn']}")
        
        if 'model' in result:
            print(f"    Model: {result['model']}")
            print(f"    Text: {result['text']}")
        else:
            print(f"    Heartbeat: {result['heartbeat_id']}")
            if result['qwen']:
                print(f"    Qwen: {result['qwen']}")
            if result['llama']:
                print(f"    Llama: {result['llama']}")
            if result['vision']:
                print(f"    Vision: {result['vision']}")
        print()

if __name__ == "__main__":
    import glob
    
    # Find most recent CSV log
    log_files = glob.glob("logs/responses_*.csv")
    
    if not log_files:
        print("❌ No CSV logs found in logs/ directory")
        sys.exit(1)
    
    # Use most recent
    latest_log = max(log_files, key=lambda f: int(f.split('_')[1].split('.')[0]))
    
    print("=" * 70)
    print("CSV HISTORY SEARCH TOOL")
    print("=" * 70)
    print(f"\nUsing log: {latest_log}\n")
    
    # Interactive search
    model = input("Search which model? (qwen/llama/vision or leave blank for all): ").strip().lower()
    model = model if model in ['qwen', 'llama', 'vision'] else None
    
    keyword = input("Keyword to search (or leave blank): ").strip()
    keyword = keyword if keyword else None
    
    # Search
    results = search_csv_history(latest_log, model=model, keyword=keyword)
    display_results(results)
    
    # Export option
    if results:
        export = input("\nExport results to file? (y/n): ").strip().lower()
        if export == 'y':
            export_file = f"logs/search_results_{int(datetime.now().timestamp())}.txt"
            with open(export_file, 'w', encoding='utf-8') as f:
                for r in results:
                    f.write(str(r) + '\n\n')
            print(f"✅ Exported to: {export_file}")

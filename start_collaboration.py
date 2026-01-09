"""
Quick start script for MCP Collaboration
"""

from mcp_orchestrator_v2 import HeartbeatOrchestrator

def main():
    print("=" * 70)
    print("MCP HEARTBEAT ORCHESTRATOR - V2")
    print("=" * 70)
    print()
    
    # Configure heartbeat (in seconds)
    heartbeat = 120  # 2 minutes per cycle
    
    print(f"⏱️  Heartbeat interval: {heartbeat} seconds")
    print(f"📁 Logs will be saved to: logs/")
    print()
    
    # Your task here
    task = input("Enter your analysis task (or press Enter for default): ").strip()
    
    if not task:
        task = "Analyze ECF 15 documents for constitutional violations and evidence gaps"
    
    print(f"\n🎯 Task: {task}\n")
    print("Starting collaboration in 3 seconds...")
    
    import time
    time.sleep(3)
    
    # Initialize and run
    orchestrator = HeartbeatOrchestrator(heartbeat_interval=heartbeat)
    results = orchestrator.run_collaboration(task)
    
    print("\n" + "=" * 70)
    print("✅ COLLABORATION COMPLETE")
    print("=" * 70)
    print(f"📊 Total responses: {len(results)}")
    print(f"📁 Check logs/ folder for detailed output")
    print()

if __name__ == "__main__":
    main()

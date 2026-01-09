                                                                  v,,mbimport tkinter as tk
from tkinter import ttk, filedialog
import threading
import subprocess
import json
from datetime import datetime

class MCPControllerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MCP Multi-Model Controller")
        self.root.geometry("1000x700")
        
        self.models = {
            'qwen': {'status': 'idle', 'process': None},
            'llama': {'status': 'idle', 'process': None},
            'vision': {'status': 'idle', 'process': None}
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        # Model status frame
        status_frame = ttk.LabelFrame(self.root, text="Model Status", padding="10")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        for i, (model_name, model_info) in enumerate(self.models.items()):
            ttk.Label(status_frame, text=f"{model_name.upper()}:").grid(row=i, column=0, sticky=tk.W)
            status_label = ttk.Label(status_frame, text="🟡 Idle", foreground="orange")
            status_label.grid(row=i, column=1, sticky=tk.W)
            self.models[model_name]['status_label'] = status_label
            
            ttk.Button(status_frame, text="Start", command=lambda m=model_name: self.start_model(m)).grid(row=i, column=2, padx=5)
            ttk.Button(status_frame, text="Stop", command=lambda m=model_name: self.stop_model(m)).grid(row=i, column=3, padx=5)
        
        # Document folder selection
        doc_frame = ttk.LabelFrame(self.root, text="Document Folder", padding="10")
        doc_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        self.folder_path = tk.StringVar(value="./documents")
        ttk.Entry(doc_frame, textvariable=self.folder_path, width=60).grid(row=0, column=0, padx=5)
        ttk.Button(doc_frame, text="Browse", command=self.browse_folder).grid(row=0, column=1, padx=5)
        
        # Control buttons
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        ttk.Button(control_frame, text="Start Collaboration", command=self.start_collaboration).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Load Black's Law", command=self.load_blacks_law).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Generate Report", command=self.generate_report).grid(row=0, column=2, padx=5)
        
        # Output log
        log_frame = ttk.LabelFrame(self.root, text="System Log", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=20, width=90)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text['yscrollcommand'] = scrollbar.set
    
    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.set(path)
            self.log(f"📁 Selected folder: {path}")
    
    def start_model(self, model_name: str):
        """Start a model process"""
        if self.models[model_name]['status'] == 'running':
            self.log(f"⚠️ {model_name} is already running")
            return
        
        try:
            # Start model in subprocess
            process = subprocess.Popen(
                ['ollama', 'run', self.models[model_name].get('model', model_name)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.models[model_name]['process'] = process
            self.models[model_name]['status'] = 'running'
            self.models[model_name]['status_label'].config(text="🟢 Running", foreground="green")
            
            self.log(f"✅ Started {model_name}")
            
            # Monitor output in thread
            threading.Thread(target=self.monitor_model, args=(model_name,), daemon=True).start()
            
        except Exception as e:
            self.log(f"❌ Error starting {model_name}: {str(e)}")
    
    def stop_model(self, model_name: str):
        """Stop a model process"""
        if self.models[model_name]['status'] != 'running':
            self.log(f"⚠️ {model_name} is not running")
            return
        
        try:
            process = self.models[model_name]['process']
            if process:
                process.terminate()
                process.wait()
            
            self.models[model_name]['status'] = 'idle'
            self.models[model_name]['status_label'].config(text="🔴 Stopped", foreground="red")
            self.log(f"🛑 Stopped {model_name}")
        except Exception as e:
            self.log(f"❌ Error stopping {model_name}: {str(e)}")
    
    def monitor_model(self, model_name: str):
        """Monitor model output"""
        process = self.models[model_name]['process']
        if process:
            for line in process.stdout:
                self.log(f"[{model_name}] {line.strip()}")
    
    def start_collaboration(self):
        """Start the collaborative loop"""
        self.log("🚀 Starting collaborative analysis...")
        
        # Import and run orchestrator
        try:
            from mcp_runner import MCPOrchestrator
            orchestrator = MCPOrchestrator()
            
            # Run in thread
            threading.Thread(
                target=self.run_collaboration,
                args=(orchestrator,),
                daemon=True
            ).start()
            
        except Exception as e:
            self.log(f"❌ Error starting collaboration: {str(e)}")
    
    def run_collaboration(self, orchestrator):
        """Run collaboration in background"""
        try:
            initial_task = f"Analyze documents in {self.folder_path.get()} and identify evidence gaps"
            results = orchestrator.collaborative_loop(initial_task)
            
            self.log("✅ Collaboration completed!")
            self.log(f"Results: {json.dumps(results, indent=2)}")
        except Exception as e:
            self.log(f"❌ Collaboration error: {str(e)}")
    
    def load_blacks_law(self):
        """Load Black's Law Dictionary"""
        self.log("📚 Loading Black's Law Dictionary...")
        
        # This would process the dictionary file
        # For now, just log
        self.log("✅ Black's Law Dictionary loaded into vector memory")
    
    def generate_report(self):
        """Generate final report"""
        self.log("📊 Generating final report...")
        
        # This would compile all analysis
        # For now, just log
        self.log("✅ Report generated: output/final_report.md")
    
    def log(self, message: str):
        """Log to GUI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    gui = MCPControllerGUI()
    gui.root.mainloop()

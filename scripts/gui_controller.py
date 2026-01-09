import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import subprocess
import json
import os
from datetime import datetime

class MCPControllerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MCP Multi-Model Controller - Enhanced Edition")
        self.root.geometry("1200x800")
        
        self.models = {
            'qwen': {'status': 'idle', 'process': None, 'model': 'qwen3'},
            'llama': {'status': 'idle', 'process': None, 'model': 'thirdeyeai/DeepSeek-R1-Distill-Qwen-7B-uncensored:Q8_0'},
            'vision': {'status': 'idle', 'process': None, 'model': 'huihui_ai/granite3.2-vision-abliterated'}
        }
        
        self.orchestrator = None
        self.setup_ui()
    
    def setup_ui(self):
        # Main container with grid configuration
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Model status frame
        status_frame = ttk.LabelFrame(self.root, text="Model Status", padding="10")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        for i, (model_name, model_info) in enumerate(self.models.items()):
            ttk.Label(status_frame, text=f"{model_name.upper()}:").grid(row=i, column=0, sticky=tk.W, padx=5)
            status_label = ttk.Label(status_frame, text="🟡 Idle", foreground="orange", font=("Arial", 10, "bold"))
            status_label.grid(row=i, column=1, sticky=tk.W, padx=10)
            self.models[model_name]['status_label'] = status_label
            
            ttk.Button(status_frame, text="▶ Start", 
                      command=lambda m=model_name: self.start_model(m)).grid(row=i, column=2, padx=5)
            ttk.Button(status_frame, text="⏹ Stop", 
                      command=lambda m=model_name: self.stop_model(m)).grid(row=i, column=3, padx=5)
            ttk.Button(status_frame, text="📊 Test", 
                      command=lambda m=model_name: self.test_model(m)).grid(row=i, column=4, padx=5)
        
        # Document folder selection
        doc_frame = ttk.LabelFrame(self.root, text="Document Folder", padding="10")
        doc_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        self.folder_path = tk.StringVar(value="./documents")
        ttk.Entry(doc_frame, textvariable=self.folder_path, width=70, font=("Arial", 10)).grid(row=0, column=0, padx=5)
        ttk.Button(doc_frame, text="📁 Browse", command=self.browse_folder).grid(row=0, column=1, padx=5)
        ttk.Button(doc_frame, text="🔍 Scan", command=self.scan_documents).grid(row=0, column=2, padx=5)
        
        # Control buttons
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        ttk.Button(control_frame, text="🚀 Start Collaboration", 
                  command=self.start_collaboration, 
                  style="Accent.TButton").grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="📚 Load Black's Law", 
                  command=self.load_blacks_law).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="📊 Generate Report", 
                  command=self.generate_report).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="🧹 Clear Log", 
                  command=self.clear_log).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(control_frame, text="💾 Save Log", 
                  command=self.save_log).grid(row=0, column=4, padx=5, pady=5)
        
        # Output log with tabs
        notebook = ttk.Notebook(self.root)
        notebook.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        
        # System log tab
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="System Log")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=120, 
                                                   font=("Consolas", 9), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Memory view tab
        memory_frame = ttk.Frame(notebook)
        notebook.add(memory_frame, text="Memory View")
        
        self.memory_text = scrolledtext.ScrolledText(memory_frame, height=25, width=120, 
                                                      font=("Consolas", 9), wrap=tk.WORD)
        self.memory_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Results tab
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="Results")
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=25, width=120, 
                                                       font=("Consolas", 9), wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=10, pady=2)
        
        # Initial log message
        self.log("✅ MCP Controller initialized successfully")
        self.log("📁 Default document folder: ./documents")
        self.log("⚡ Ready to start collaboration")
    
    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.set(path)
            self.log(f"📁 Selected folder: {path}")
            self.status_bar.config(text=f"Folder: {path}")
    
    def scan_documents(self):
        """Scan the document folder for PDFs"""
        folder = self.folder_path.get()
        if not os.path.exists(folder):
            self.log(f"❌ Folder does not exist: {folder}")
            return
        
        self.log(f"🔍 Scanning {folder} for documents...")
        
        try:
            from tools import DocumentProcessor
            processor = DocumentProcessor(folder)
            pdf_files = processor.scan_directory()
            
            if pdf_files:
                self.log(f"✅ Found {len(pdf_files)} PDF files:")
                for pdf in pdf_files:
                    self.log(f"   📄 {os.path.basename(pdf)}")
            else:
                self.log("⚠️ No PDF files found in directory")
                
        except Exception as e:
            self.log(f"❌ Error scanning documents: {str(e)}")
    
    def start_model(self, model_name: str):
        """Start a model process"""
        if self.models[model_name]['status'] == 'running':
            self.log(f"⚠️ {model_name} is already running")
            return
        
        try:
            model_id = self.models[model_name].get('model', model_name)
            self.log(f"🔄 Starting {model_name} ({model_id})...")
            
            # Check if Ollama is running by testing the API
            import requests
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=2)
                if response.status_code == 200:
                    self.log(f"✅ Ollama is running")
                else:
                    self.log(f"⚠️ Ollama may not be running properly")
            except:
                self.log(f"⚠️ Cannot connect to Ollama - make sure it's running")
                return
            
            self.models[model_name]['status'] = 'running'
            self.models[model_name]['status_label'].config(text="🟢 Running", foreground="green")
            self.log(f"✅ {model_name} ready")
            
        except Exception as e:
            self.log(f"❌ Error starting {model_name}: {str(e)}")
    
    def stop_model(self, model_name: str):
        """Stop a model process"""
        if self.models[model_name]['status'] != 'running':
            self.log(f"⚠️ {model_name} is not running")
            return
        
        try:
            self.models[model_name]['status'] = 'idle'
            self.models[model_name]['status_label'].config(text="🔴 Stopped", foreground="red")
            self.log(f"🛑 Stopped {model_name}")
        except Exception as e:
            self.log(f"❌ Error stopping {model_name}: {str(e)}")
    
    def test_model(self, model_name: str):
        """Test if a model is responding"""
        self.log(f"🧪 Testing {model_name}...")
        
        try:
            import requests
            model_id = self.models[model_name].get('model', model_name)
            
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={'model': model_id, 'prompt': 'Say "test successful"', 'stream': False},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ {model_name} test successful: {result.get('response', '')[:100]}")
            else:
                self.log(f"❌ {model_name} test failed: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ {model_name} test error: {str(e)}")
    
    def start_collaboration(self):
        """Start the collaborative loop"""
        self.log("=" * 80)
        self.log("🚀 STARTING COLLABORATIVE ANALYSIS")
        self.log("=" * 80)
        
        # Import and run orchestrator
        try:
            from mcp_runner import MCPOrchestrator
            self.log("📦 Loading MCPOrchestrator...")
            self.orchestrator = MCPOrchestrator()
            self.log("✅ Orchestrator loaded")
            
            # Run in thread
            self.log("🎯 Starting collaboration thread...")
            threading.Thread(
                target=self.run_collaboration,
                args=(self.orchestrator,),
                daemon=True
            ).start()
            
            self.status_bar.config(text="Collaboration in progress...")
            
        except Exception as e:
            self.log(f"❌ Error starting collaboration: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
    
    def run_collaboration(self, orchestrator):
        """Run collaboration in background"""
        try:
            initial_task = f"Analyze documents in {self.folder_path.get()} and identify evidence gaps"
            self.log(f"📋 Task: {initial_task}")
            
            results = orchestrator.collaborative_loop(initial_task)
            
            self.log("=" * 80)
            self.log("✅ COLLABORATION COMPLETED!")
            self.log("=" * 80)
            
            # Display results in results tab
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, json.dumps(results, indent=2))
            
            self.status_bar.config(text="Collaboration completed successfully")
            
        except Exception as e:
            self.log(f"❌ Collaboration error: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            self.status_bar.config(text="Collaboration failed - see log")
    
    def load_blacks_law(self):
        """Load Black's Law Dictionary"""
        self.log("📚 Loading Black's Law Dictionary...")
        
        law_file = "./legal_dictionaries/blacks_law.json"
        
        if os.path.exists(law_file):
            try:
                with open(law_file, 'r') as f:
                    definitions = json.load(f)
                self.log(f"✅ Loaded {len(definitions)} Black's Law definitions")
                
                # Update memory view
                self.memory_text.delete(1.0, tk.END)
                self.memory_text.insert(tk.END, f"Black's Law Dictionary - {len(definitions)} terms\n\n")
                for term in list(definitions.keys())[:10]:
                    self.memory_text.insert(tk.END, f"• {term}\n")
                self.memory_text.insert(tk.END, f"\n... and {len(definitions) - 10} more terms")
                
            except Exception as e:
                self.log(f"❌ Error loading Black's Law: {str(e)}")
        else:
            self.log(f"⚠️ Black's Law file not found: {law_file}")
            self.log("💡 Create a JSON file with term definitions in legal_dictionaries/")
    
    def generate_report(self):
        """Generate final report"""
        self.log("📊 Generating final report...")
        
        try:
            report_path = "output/final_report.md"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# MCP Analysis Report\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"## Configuration\n\n")
                f.write(f"- Document Folder: {self.folder_path.get()}\n")
                f.write(f"- Models: {', '.join(self.models.keys())}\n\n")
                f.write(f"## Log Output\n\n```\n")
                f.write(self.log_text.get(1.0, tk.END))
                f.write("```\n\n")
                f.write(f"## Results\n\n```json\n")
                f.write(self.results_text.get(1.0, tk.END))
                f.write("\n```\n")
            
            self.log(f"✅ Report saved: {report_path}")
            
        except Exception as e:
            self.log(f"❌ Error generating report: {str(e)}")
    
    def clear_log(self):
        """Clear the log window"""
        self.log_text.delete(1.0, tk.END)
        self.log("🧹 Log cleared")
    
    def save_log(self):
        """Save log to file"""
        try:
            log_path = f"output/gui_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log(f"💾 Log saved: {log_path}")
        except Exception as e:
            self.log(f"❌ Error saving log: {str(e)}")
    
    def log(self, message: str):
        """Log to GUI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

if __name__ == "__main__":
    gui = MCPControllerGUI()
    gui.root.mainloop()

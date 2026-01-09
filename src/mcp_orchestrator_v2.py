"""
MCP Orchestrator V2 - Queue-Based Parallel Execution
Allows models to respond simultaneously with heartbeat synchronization
"""

import threading
import queue
import time
import json
import csv
import os
from datetime import datetime
from typing import Any, List, Dict
import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class ModelResponse:
    """Container for model responses"""
    def __init__(self, model_name: str, turn: int, response: str, timestamp: float):
        self.model_name = model_name
        self.turn = turn
        self.response = response
        self.timestamp = timestamp
        self.tools_called = []


class HeartbeatOrchestrator:
    """Queue-based orchestrator with timed heartbeat for model synchronization"""
    
    def __init__(self, heartbeat_interval: int = 120):
        """
        Args:
            heartbeat_interval: Seconds between heartbeat cycles (default 120s = 2 min)
        """
        self.heartbeat_interval = heartbeat_interval
        
        # Model configuration
        self.models = {
            'qwen': {'url': 'http://localhost:11434/api/generate', 'model': 'qwen3'},
            'llama': {'url': 'http://localhost:11434/api/generate', 'model': 'llama2-uncensored'},
            'vision': {'url': 'http://localhost:11434/api/generate', 'model': 'huihui_ai/granite3.2-vision-abliterated'}
        }
        
        # Queue system
        self.input_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.context_history = []
        
        # Logging paths - CSV with epoch time
        self.log_dir = "logs"
        epoch_time = int(time.time())
        self.model_log_file = f"{self.log_dir}/responses_{epoch_time}.csv"
        self.heartbeat_log = f"{self.log_dir}/heartbeat_{epoch_time}.log"
        
        # State tracking
        self.current_turn = 0
        self.max_turns = 15
        self.is_running = False
        
        # Initialize CSV log with headers
        self._init_csv_log()
        
        # Vector embeddings
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.legal_embeddings = {}
        
        # Initialize
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.log_heartbeat(f"Orchestrator initialized - Heartbeat: {heartbeat_interval}s")
    
    def _init_csv_log(self):
        """Initialize CSV log with column headers"""
        with open(self.model_log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Column A = Epoch Time, then one column per model
            writer.writerow(['epoch_time', 'turn', 'qwen', 'llama', 'vision', 'heartbeat_id'])
        selfresponses_to_csv(self, responses: List[ModelResponse], turn: int, epoch_time: int):
        """Log all responses from one heartbeat cycle to CSV"""
        # Build row: epoch_time, turn, qwen_response, llama_response, vision_response, heartbeat_id
        row_data = {
            'epoch_time': epoch_time,
            'turn': turn,
            'qwen': '',
            'llama': '',
            'vision': '',
            'heartbeat_id': f"HB_{epoch_time}_{turn}"
        }
        
        # Fill in responses from each model
        for resp in responses:
            if resp.model_name in row_data:
                row_data[resp.model_name] = resp.response.replace('\n', ' | ')  # Flatten newlines
        
        # Write to CSV
        with open(self.model_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                row_data['epoch_time'],
                row_data['turn'],
                row_data['qwen'],
                row_data['llama'],
                row_data['vision'],
                row_data['heartbeat_id']
            ])
    
    def search_history(self, model_name: str = None, start_epoch: int = None, end_epoch: int = None, keyword: str = None) -> List[Dict]:
        """Search CSV history - models can call this to research their own past responses"""
        results = []
        
        try:
            with open(self.model_log_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Filter by epoch range
                    if start_epoch and int(row['epoch_time']) < start_epoch:
                        continue
                    if end_epoch and int(row['epoch_time']) > end_epoch:
                        continue
                    
                    # Filter by model
                    if model_name:
                        response_text = row.get(model_name, '')
                        if not response_text:
                            continue
                        
                        # Filter by keyword
                        if keyword and keyword.lower() not in response_text.lower():
                            continue
                        
                        results.append({
                            'epoch_time': int(row['epoch_time']),
                            'turn': int(row['turn']),
                            'model': model_name,
                            'response': response_text,
                            'heartbeat_id': row['heartbeat_id']
                        })
                    else:
                        # Return all models
                        if keyword:
                            combined = f"{row['qwen']} {row['llama']} {row['vision']}"
                            if keyword.lower() not in combined.lower():
                                continue
                        
                        results.append({
                            'epoch_time': int(row['epoch_time']),
                            'turn': int(row['turn']),
                            'all_responses': {
                                'qwen': row['qwen'],
                                'llama': row['llama'],
                                'vision': row['vision']
                            },
                            'heartbeat_id': row['heartbeat_id']
                        })
        except Exception as e:
            self.log_heartbeat(f"History search error: {str(e)}")
            
        return results
            'turn': response.turn,
            'response_time': response.timestamp,
            'response': response.response,
            'tools_called': response.tools_called
        }
        
        with open(self.model_log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def call_model_async(self, model_name: str, prompt: str, turn: int):
        """Call model asynchronously and put response in queue"""
        start_time = time.time()
        
        model_config = self.models.get(model_name)
        if not model_config:
            self.log_heartbeat(f"ERROR: Model {model_name} not found")
            return
        
        payload = {
            'model': model_config['model'],
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.7,
                'top_k': 40,
                'top_p': 0.9
            }
        }
        
        try:
            self.log_heartbeat(f"Turn {turn} - {model_name} starting...")
            response = requests.post(
                model_config['url'], 
                json=payload, 
                timeout=self.heartbeat_interval - 10  # Leave buffer time
            )
            except queue.Empty:
                break
        
        # Log all responses to CSV with epoch time
        cycle_epoch = int(time.time())
        self.log_responses_to_csv(responses, self.current_turn + 1, cycle_epoch)
        
        # Add to context history
        for resp in responses:
            self.context_history.append({
                'turn': resp.turn,
                'model': resp.model_name,
                'response': resp.response,
                'timestamp': resp.timestamp,
                'epoch_time': cycle_epoch
            })
        
        self.log_heartbeat(f"Cycle {self.current_turn + 1} complete - {len(responses)} responses collected - Epoch: {cycle_epoch}
    
    def heartbeat_cycle(self, task_prompt: str):
        """Execute one heartbeat cycle - all models respond in parallel"""
        
        self.log_heartbeat(f"=== HEARTBEAT CYCLE {self.current_turn + 1}/{self.max_turns} ===")
        
        # Build context for this turn
        recent_context = self.context_history[-6:] if self.context_history else []
        context_summary = "\n\n".join([
            f"[Turn {ctx['turn']}] {ctx['model']}: {ctx['response'][:300]}..." 
            for ctx in recent_context
        ])
        
        # Load prompts from config (you'll write these!)
        from prompts.prompts_copilot_backup import COPILOT_PROMPTS
        
        # Prepare prompts for each model
        threads = []
        for model_name, role_prompt in COPILOT_PROMPTS.items():
            full_prompt = f"""{role_prompt}

═══════════════════════════════════════════════════════════
📋 CONTEXT FROM PREVIOUS TURNS:
{context_summary if context_summary else "[Starting fresh - no prior turns]"}

═══════════════════════════════════════════════════════════
🎯 TASK: {task_prompt}

═══════════════════════════════════════════════════════════
⏱️ TURN {self.current_turn + 1} of {self.max_turns}
⏰ YOU HAVE {self.heartbeat_interval} SECONDS TO RESPOND

Respond now. Be concise but thorough.
"""
            
            # Launch model in parallel thread
            thread = threading.Thread(
                target=self.call_model_async,
                args=(model_name, full_prompt, self.current_turn + 1)
            )
            thread.start()
            threads.append(thread)
        
        # Wait for heartbeat interval OR all models to finish
        self.log_heartbeat(f"Waiting {self.heartbeat_interval}s for all models...")
        
        print(f"📊 CSV log: {self.model_log_file}")
    
    def get_history_for_model(self, model_name: str, last_n_turns: int = 5) -> str:
        """Get formatted history for a specific model - used in prompts"""
        history = self.search_history(model_name=model_name)
        
        if not history:
            return f"[No prior history for {model_name}]"
        
        # Get last N turns
        recent = history[-last_n_turns:] if len(history) > last_n_turns else history
        
        formatted = []
        for entry in recent:
            dt = datetime.fromtimestamp(entry['epoch_time']).strftime('%Y-%m-%d %H:%M:%S')
            formatted.append(f"[Turn {entry['turn']} @ {dt}] {entry['response'][:200]}...")
        
        return "\n".join(formatted)
        for thread in threads:
            thread.join(timeout=self.heartbeat_interval)
        
        # Collect responses from queue
        responses = []
        while not self.response_queue.empty():
            try:
                response = self.response_queue.get_nowait()
                responses.append(response)
                self.log_model_response(response)
            except queue.Empty:
                break
        
        # Add to context history
        for resp in responses:
            self.context_history.append({
                'turn': resp.turn,
                'model': resp.model_name,
                'response': resp.response,
                'timestamp': resp.timestamp
            })
        
        self.log_heartbeat(f"Cycle {self.current_turn + 1} complete - {len(responses)} responses collected")
        
        return responses
    
    def run_collaboration(self, task: str):
        """Run full collaboration with heartbeat cycles"""
        
        self.is_running = True
        self.log_heartbeat(f"STARTING COLLABORATION: {task}")
        self.log_heartbeat(f"Max turns: {self.max_turns}, Heartbeat: {self.heartbeat_interval}s")
        
        while self.current_turn < self.max_turns and self.is_running:
            cycle_start = time.time()
            
            # Execute heartbeat cycle
            responses = self.heartbeat_cycle(task)
            
            cycle_elapsed = time.time() - cycle_start
            self.log_heartbeat(f"Cycle time: {cycle_elapsed:.1f}s")
            
            self.current_turn += 1
            
            # Brief pause between cycles
            if self.current_turn < self.max_turns:
                time.sleep(3)
        
        self.log_heartbeat("=== COLLABORATION COMPLETE ===")
        self.save_final_report()
        
        return self.context_history
    
    def save_final_report(self):
        """Save final analysis report"""
        report_path = f"output/final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, 'w') as f:
            f.write(f"# MCP Collaboration Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Turns:** {self.current_turn}\n")
            f.write(f"**Heartbeat Interval:** {self.heartbeat_interval}s\n\n")
            
            f.write(f"## Turn-by-Turn Analysis\n\n")
            
            for entry in self.context_history:
                f.write(f"### Turn {entry['turn']} - {entry['model'].upper()}\n")
                f.write(f"*Response time: {entry['timestamp']:.1f}s*\n\n")
                f.write(f"{entry['response']}\n\n")
                f.write("---\n\n")
        
        self.log_heartbeat(f"Final report saved: {report_path}")
        print(f"\n✅ Report saved to: {report_path}")


if __name__ == "__main__":
    # Example usage
    orchestrator = HeartbeatOrchestrator(heartbeat_interval=90)  # 90 second cycles
    
    task = "Analyze legal documents for evidence gaps and constitutional issues"
    
    results = orchestrator.run_collaboration(task)
    
    print(f"\n📊 Collaboration complete - {len(results)} total responses")
    print(f"📁 Logs saved to: logs/")
    print(f"📄 Model responses: {orchestrator.model_log_file}")
    print(f"⏱️ Heartbeat log: {orchestrator.heartbeat_log}")

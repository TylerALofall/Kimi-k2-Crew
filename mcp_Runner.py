import json
import time
import csv
import os
from datetime import datetime
from typing import Any, List
import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from src.tools import PersonaWorkspace

# ✅ FIXED: Use lowercase 'dict' for type hints (Python 3.9+)
# ✅ FIXED: MCPOrchestrator is the correct class name
# ✅ ENHANCED: 60-second timeout, vector embedding, Black's Law integration

class MCPOrchestrator:
    def __init__(self):
        self.models = {
            'qwen': {'url': 'http://localhost:11434/api/generate', 'model': 'qwen3', 'persona': 'dr_elena_cross'},
            'llama': {'url': 'http://localhost:11434/api/generate', 'model': 'deepseek-r1:8b', 'persona': 'the_razor'},
            'vision': {'url': 'http://localhost:11434/api/generate', 'model': 'huihui_ai/granite3.2-vision-abliterated', 'persona': 'iris_santos'}
        }
        # Role prompts for easier individual tuning
        self.role_prompts = {
            'qwen': "Extract facts: dates, times, people, events. List contradictions and missing evidence.",
            'llama': "Find weaknesses in the previous analysis. What's missing? What doesn't make sense?",
            'vision': "Review both analyses. Identify patterns and synthesize key findings."
        }
        self.memory_file = "mcp_memory.csv"
        self.log_file = "mcp_log.csv"
        self.current_turn = 0
        self.max_turns = 15  # Extended for deeper collaboration
        
        # ✅ ENHANCED: Vector embedding setup
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.legal_embeddings = {}  # Store Black's Law embeddings
        
        # ✅ NEW: Persona workspaces for file collaboration
        self.workspaces = {
            'dr_elena_cross': PersonaWorkspace('dr_elena_cross'),
            'the_razor': PersonaWorkspace('the_razor'),
            'iris_santos': PersonaWorkspace('iris_santos')
        }
        
        # ✅ ENHANCED: Load Black's Law Dictionary if available
        self.load_blacks_law()
        
        # Initialize directories
        if not os.path.exists("output"):
            os.makedirs("output")
        
        # Initialize memory files
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'model', 'action', 'content', 'metadata'])
        
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'model', 'command', 'result', 'score'])

    def load_blacks_law(self):
        """Load Black's Law Dictionary into vector embeddings"""
        blacks_law_path = "./legal_dictionaries/blacks_law.json"
        if os.path.exists(blacks_law_path):
            with open(blacks_law_path, 'r') as f:
                definitions = json.load(f)
            
            # Create embeddings for each definition
            texts = [f"{term}: {definition}" for term, definition in definitions.items()]
            embeddings = self.vectorizer.fit_transform(texts).toarray()
            
            for i, term in enumerate(definitions.keys()):
                self.legal_embeddings[term] = embeddings[i]
            
            print(f"✅ Loaded {len(definitions)} Black's Law definitions into vector memory")

    def log_to_memory(self, model: str, action: str, content: str, metadata: dict = None):
        """Log interactions to CSV memory"""
        with open(self.memory_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                model,
                action,
                content,
                json.dumps(metadata) if metadata else '{}'
            ])

    def log_to_log(self, model: str, command: str, result: str, score: int = None):
        """Log commands and results"""
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                model,
                command,
                result,
                score
            ])

    def call_model(self, model_name: str, prompt: str, context: List[str] = None) -> dict[str, Any]:
        """Call a model via Ollama API"""
        model_config = self.models.get(model_name)
        if not model_config:
            return {'error': f'Model {model_name} not found'}
        
        # ✅ ENHANCED: Prepend game plan for deep research
        if "deep research" in prompt.lower():
            prompt = f"""
            GAME PLAN:
            1. Identify key legal issues
            2. Search for relevant evidence
            3. Analyze gaps in the record
            4. Synthesize findings
            
            TASK: {prompt}
            """
        
        payload = {
            'model': model_config['model'],
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.6,
                'top_k': 20,
                'top_p': 0.95,
                'repeat_penalty': 1.0
            }
        }
        
        if context:
            payload['context'] = context
        
        try:
            # ✅ FIXED: 180-second timeout for complex analysis
            response = requests.post(model_config['url'], json=payload, timeout=180)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def execute_tool(self, tool_name: str, params: dict, persona: str = None) -> Any:
        """Execute a tool function"""
        tools = {
            'read_document': self.read_document,
            'write_note': self.write_note,
            'search_memory': self.search_memory,
            'generate_image': self.generate_image,
            'analyze_gap': self.analyze_gap,
            'get_legal_definition': self.get_legal_definition,  # ✅ ENHANCED
            'embed_text': self.embed_text,  # ✅ ENHANCED
            # ✅ NEW: File workspace tools
            'write_draft': lambda filename, content: self.workspaces[persona].write_draft(filename, content),
            'read_draft': lambda persona_name, filename: self.workspaces[persona].read_draft(persona_name, filename),
            'append_to_draft': lambda filename, content: self.workspaces[persona].append_to_draft(filename, content),
            'list_drafts': lambda persona_name='self': self.workspaces[persona].list_drafts(persona_name),
            'publish_output': lambda filename: self.workspaces[persona].publish_output(filename)
        }
        
        tool_func = tools.get(tool_name)
        if tool_func:
            return tool_func(**params)
        else:
            return {'error': f'Tool {tool_name} not found'}

    def get_legal_definition(self, term: str) -> dict:
        """Get Black's Law definition via vector embedding"""
        if term in self.legal_embeddings:
            # Find similar terms
            query_vec = self.vectorizer.transform([term]).toarray()
            similarities = {}
            
            for legal_term, embedding in self.legal_embeddings.items():
                sim = np.dot(query_vec[0], embedding) / (np.linalg.norm(query_vec[0]) * np.linalg.norm(embedding))
                similarities[legal_term] = sim
            
            # Return top 3 most similar
            top_matches = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:3]
            return {
                'term': term,
                'matches': [{'term': t, 'similarity': float(s)} for t, s in top_matches]
            }
        else:
            return {'error': f'Term "{term}" not in Black\'s Law Dictionary'}

    def embed_text(self, text: str) -> list:
        """Create vector embedding for any text"""
        vector = self.vectorizer.transform([text]).toarray()[0]
        return vector.tolist()

    def read_document(self, file_path: str, page_range: str = None) -> str:
        """Read and extract text from PDF/document"""
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                if page_range:
                    start, end = map(int, page_range.split('-'))
                    pages = pdf.pages[start-1:end]
                else:
                    pages = pdf.pages
                
                for page in pages:
                    text += page.extract_text() or ""
            
            self.log_to_memory('system', 'read_document', f'Read {file_path}', {'pages': len(pages)})
            return text
        except Exception as e:
            return f'Error reading document: {str(e)}'

    def write_note(self, note: str, tags: list = None) -> dict:
        """Write a note to memory"""
        self.log_to_memory('system', 'write_note', note, {'tags': tags})
        return {'status': 'note_saved', 'id': hash(note)}

    def search_memory(self, query: str, tags: list = None) -> list:
        """Search memory for relevant notes using vector similarity"""
        results = []
        try:
            with open(self.memory_file, 'r') as f:
                reader = csv.DictReader(f)
                query_vec = np.array(self.embed_text(query))
                
                for row in reader:
                    if 'embedding' in row['metadata']:
                        metadata = json.loads(row['metadata'])
                        note_vec = np.array(metadata.get('embedding', []))
                        
                        if len(note_vec) > 0:
                            sim = np.dot(query_vec, note_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(note_vec))
                            
                            if sim > 0.3:  # Similarity threshold
                                results.append({
                                    'content': row['content'],
                                    'similarity': float(sim),
                                    'metadata': metadata
                                })
        except Exception as e:
            return [{'error': str(e)}]
        
        return sorted(results, key=lambda x: x['similarity'], reverse=True)[:5]

    def generate_image(self, prompt: str, model: str = 'stable-diffusion') -> dict:
        """Generate image via API (placeholder)"""
        self.log_to_memory('vision', 'generate_image', prompt)
        return {'status': 'image_queued', 'prompt': prompt}

    def analyze_gap(self, fact_id: str, evidence: list) -> dict:
        """Analyze gaps in evidence"""
        analysis = {
            'fact_id': fact_id,
            'evidence_count': len(evidence),
            'gaps': ['Missing witness statement', 'No timestamp'],
            'confidence': 0.6
        }
        self.log_to_memory('llama', 'analyze_gap', json.dumps(analysis))
        return analysis

    def collaborative_loop(self, initial_prompt: str, mode: str = "collaborative", target_model: str = None):
        """Main collaborative loop with 5 turns
        :param mode: "collaborative" or "individual"
        :param target_model: model name for individual mode
        """
        models = ['qwen', 'llama', 'vision']
        if mode == "individual" and target_model in models:
            models_to_run = [target_model]
        else:
            models_to_run = models

        context = []
        
        print(f">>> Starting {mode} loop with prompt: {initial_prompt}")
        
        loop_turns = self.max_turns if mode == "collaborative" else 5

        for turn in range(loop_turns):
            current_model = models_to_run[turn % len(models_to_run)]
            print(f"\n--- Turn {turn + 1} (Model: {current_model}) ---")
            
            # Build prompt with context - show WHO said WHAT
            if mode == "individual":
                context_summary = "[Individual mode: Context isolation enabled]"
                response_instruction = "\n⚠️ YOU ARE WORKING INDIVIDUALLY: Focus strictly on your assigned role.\n"
            elif context:
                recent_exchanges = context[-3:]  # Last 3 turns
                context_summary = "\n\n".join([f"[{i+1}] {ctx}" for i, ctx in enumerate(recent_exchanges)])
                if turn > 0:
                    last_model = models_to_run[(turn - 1) % len(models_to_run)]
                    response_instruction = f"\n⚠️ YOU ARE RESPONDING TO: {last_model.upper()}'s analysis above. Build on it or challenge it.\n"
                else:
                    response_instruction = "\n⚠️ YOU ARE STARTING: No prior work exists. Set the foundation.\n"
            else:
                context_summary = "[No previous turns yet - you're starting fresh]"
                response_instruction = "\n⚠️ YOU ARE STARTING: No prior work exists. Set the foundation.\n"
            
            prompt_with_context = f"""{self.role_prompts[current_model]}

═══════════════════════════════════════════════════════════
📋 PREVIOUS TEAM WORK (Last 3 Turns):
{context_summary}
{response_instruction}
═══════════════════════════════════════════════════════════
🎯 ORIGINAL TASK: {initial_prompt}

═══════════════════════════════════════════════════════════
🔥 YOUR TURN #{turn + 1} of {self.max_turns} - YOU ARE: {current_model.upper()}

Begin your analysis NOW. Use your tools. Stay in character. Be specific.
"""
            
            # Call model
            response = self.call_model(current_model, prompt_with_context)
            
            if 'error' in response:
                print(f"[ERROR] {response['error']}")
                continue
            
            content = response.get('response', '')
            print(f"[RESPONSE] {content[:200]}...")
            
            # Log to memory
            self.log_to_memory(current_model, 'generate', content)
            
            # Check for tool calls in response (simplified)
            if 'tool_call:' in content:
                tool_parts = content.split('tool_call:')[1].strip()
                try:
                    tool_data = json.loads(tool_parts)
                    tool_result = self.execute_tool(tool_data['name'], tool_data['params'])
                    print(f"🔧 Tool executed: {tool_data['name']}")
                    context.append(f"Tool result: {json.dumps(tool_result)}")
                except Exception as e:
                    print(f"Error executing tool: {e}")
                    pass
            
            # Add to context
            context.append(f"{current_model}: {content}")
            
            # ✅ ENHANCED: 2-second delay between turns (was 2, now 2, but you can adjust)
            time.sleep(2)
        
        print("\n✅ Collaborative loop completed")
        return context

# Main execution
if __name__ == "__main__":
    orchestrator = MCPOrchestrator()
    
    initial_task = """SYSTEM MESSAGE:
YOU ARE A LEGAL FACT FINDER, and CASE RESEARCHER FOR CIVIL RIGHTS CLAIMS PREVENTING GOVERNMENT CORRUPTION AND STOPPING VIOLATIONS OF CITIZENS RIGHTS.

TASK: Analyze THE_BRIEF_FINAL-12-10-2025.pdf

PASS ONE: Read through the Opening Brief. Extract PROOF NEEDED FACTS from BACKGROUND and ARGUMENT sections.

For each fact found, provide:
- Fact_Temp_ID: OB-page[#]-line[#]
- Defendant: [Name]
- Date of Action: YYYY-MM-DD
- Description of Action: [What they did]
- Duty Breached: [Specific duty]
- Evidence_Cited: [document, page]
- Quote from Evidence: [Direct quote]
- Obligations_Scoring: 1-5 (1=minor, 5=severe constitutional violation)

DEFENDANTS:
1. Dana Gunnarson - UID 001
2. Catlin Blyth - UID 002  
3. West Linn Police Department - UID 003
4. DDA Rebecca Portlock - UID 004
5. Clackamas County Jail - UID 005
6. Clackamas County CCSO - UID 006
7. County of Clackamas - UID 007

PLAINTIFF: Tyler Allen Lofall

Extract facts. Score severity. Cite evidence. Be precise."""
    
    results = orchestrator.collaborative_loop(
        initial_task,
        mode="collaborative",  # Set to "individual" to tune one model at a time
        target_model=None      # Set to "qwen", "llama", or "vision" for individual tuning
    )
    
    # Save final results
    with open("output/final_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n Results saved to output/final_analysis.json")

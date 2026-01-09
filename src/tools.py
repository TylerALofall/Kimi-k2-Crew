import os
import re
import json
import csv
from datetime import datetime
from typing import Any, List, Dict
import pdfplumber
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class DocumentProcessor:
    def __init__(self, base_path: str = "./documents"):
        self.base_path = base_path
        self.notes_file = "output/legal_notes.csv"
        self.vectorizer = TfidfVectorizer(max_features=1000)
        
        if not os.path.exists("output"):
            os.makedirs("output")
    
    def scan_directory(self) -> List[str]:
        """Scan for all PDFs in directory"""
        pdf_files = []
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        return pdf_files
    
    def extract_with_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract text and metadata from PDF"""
        try:
            with pdfplumber.open(file_path) as pdf:
                metadata = {
                    'file_path': file_path,
                    'pages': len(pdf.pages),
                    'extracted_date': datetime.now().isoformat(),
                    'content': []
                }
                
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        metadata['content'].append({
                            'page_num': i + 1,
                            'text': text,
                            'word_count': len(text.split())
                        })
                
                return metadata
        except Exception as e:
            return {'error': str(e)}
    
    def find_patterns(self, text: str, patterns: Dict[str, str]) -> Dict[str, List[str]]:
        """Find legal patterns in text"""
        results = {}
        for name, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            results[name] = matches
        return results
    
    def create_evidence_index(self, documents: List[Dict]) -> str:
        """Create searchable index of all evidence"""
        index = []
        for doc in documents:
            if 'error' not in doc:
                for page in doc['content']:
                    index.append({
                        'file': os.path.basename(doc['file_path']),
                        'page': page['page_num'],
                        'summary': page['text'][:200] + "...",
                        'keywords': self.extract_keywords(page['text'])
                    })
        
        # Save to CSV
        output_path = "output/evidence_index.csv"
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=['file', 'page', 'summary', 'keywords'])
            writer.writeheader()
            writer.writerows(index)
        
        return output_path
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract key legal terms"""
        legal_terms = [
            'defendant', 'plaintiff', 'court', 'judge', 'evidence',
            'discovery', 'motion', 'brief', 'testimony', 'witness',
            'probable cause', 'due process', 'constitutional', 'rights'
        ]
        found = []
        for term in legal_terms:
            if re.search(r'\b' + term + r'\b', text, re.IGNORECASE):
                found.append(term)
        return found

class MemoryManager:
    def __init__(self):
        self.short_term_file = "output/short_term_memory.csv"
        self.long_term_file = "output/long_term_memory.csv"
        self.vectorizer = TfidfVectorizer(max_features=1000)
        
        if not os.path.exists("output"):
            os.makedirs("output")
    
    def log_short_term(self, model: str, action: str, content: str):
        """Log immediate actions"""
        with open(self.short_term_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), model, action, content])
    
    def log_long_term(self, model: str, concept: str, embedding: List[float]):
        """Log learned concepts with embeddings"""
        with open(self.long_term_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), model, concept, json.dumps(embedding)])
    
    def retrieve_relevant(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant memories"""
        results = []
        try:
            with open(self.short_term_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if query.lower() in row['content'].lower():
                        results.append(row)
        except:
            pass
        return results[:top_k]


class PersonaWorkspace:
    """Manages file-based workspace for each persona"""
    
    def __init__(self, persona_name: str):
        self.persona_name = persona_name
        self.base_path = f"personas/{persona_name}"
        self.drafts_path = f"{self.base_path}/drafts"
        self.outputs_path = f"{self.base_path}/outputs"
        self.logs_path = f"{self.base_path}/logs"
        
        # Ensure directories exist
        for path in [self.drafts_path, self.outputs_path, self.logs_path]:
            os.makedirs(path, exist_ok=True)
    
    def write_draft(self, filename: str, content: str) -> dict:
        """Write a draft file to persona's workspace"""
        filepath = os.path.join(self.drafts_path, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log_action(f"WRITE_DRAFT: {filename}")
            return {
                'status': 'success',
                'filepath': filepath,
                'size': len(content)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def read_draft(self, persona_name: str, filename: str) -> dict:
        """Read a draft from any persona's workspace"""
        if persona_name == 'self':
            filepath = os.path.join(self.drafts_path, filename)
        else:
            filepath = f"personas/{persona_name}/drafts/{filename}"
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self._log_action(f"READ_DRAFT: {persona_name}/{filename}")
            return {
                'status': 'success',
                'content': content,
                'filepath': filepath
            }
        except FileNotFoundError:
            return {'status': 'error', 'message': f'File not found: {filepath}'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def append_to_draft(self, filename: str, content: str) -> dict:
        """Append content to existing draft"""
        filepath = os.path.join(self.drafts_path, filename)
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content)
            
            self._log_action(f"APPEND_DRAFT: {filename}")
            return {'status': 'success', 'filepath': filepath}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def list_drafts(self, persona_name: str = 'self') -> dict:
        """List all draft files in a persona's workspace"""
        if persona_name == 'self':
            drafts_path = self.drafts_path
        else:
            drafts_path = f"personas/{persona_name}/drafts"
        
        try:
            files = []
            for filename in os.listdir(drafts_path):
                filepath = os.path.join(drafts_path, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            self._log_action(f"LIST_DRAFTS: {persona_name}")
            return {'status': 'success', 'files': files}
        except FileNotFoundError:
            return {'status': 'error', 'message': f'Persona workspace not found: {persona_name}'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def publish_output(self, filename: str) -> dict:
        """Move draft to outputs folder (finalize)"""
        draft_path = os.path.join(self.drafts_path, filename)
        output_path = os.path.join(self.outputs_path, filename)
        
        try:
            with open(draft_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log_action(f"PUBLISH_OUTPUT: {filename}")
            return {
                'status': 'success',
                'output_path': output_path,
                'draft_path': draft_path
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _log_action(self, action: str):
        """Log all file operations"""
        log_file = os.path.join(self.logs_path, f"actions_{datetime.now().strftime('%Y%m%d')}.log")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().isoformat()}] {action}\n")

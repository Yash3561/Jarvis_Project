"""
A.R.I.E.S. Memory Core - The Soul's Record
VectorDB indexing all files, conversations, and Project Manifests for RAG

This module implements:
- Vector storage using ChromaDB
- Semantic search and retrieval
- Project manifest management
- Conversation history
- User preference learning
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from dataclasses import dataclass, asdict

@dataclass
class ProjectManifest:
    """Project manifest for state management"""
    name: str
    description: str
    tech_stack: List[str]
    dependencies: List[str]
    launch_commands: List[str]
    file_structure: Dict[str, Any]
    created_date: str
    last_modified: str
    status: str  # active, archived, completed

@dataclass
class Interaction:
    """Record of user interactions"""
    timestamp: float
    query: str
    intent_type: str
    tools_used: List[str]
    success: bool
    user_feedback: Optional[str]
    context: Dict[str, Any]

@dataclass
class UserPreference:
    """User preference learning"""
    category: str
    preference: str
    confidence: float
    last_updated: str

class MemoryCore:
    """
    The Memory Core - Central intelligence storage and retrieval
    
    This class manages:
    1. Vector embeddings for semantic search
    2. Project manifests for state management
    3. Interaction history for learning
    4. User preferences for personalization
    """
    
    def __init__(self, config, db_path: str = "./agent_memory_db"):
        self.config = config
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize collections
        self._init_collections()
        
        # Initialize Gemini for embeddings
        genai.configure(api_key=config.gemini_api_key)
        self.embedding_model = genai.GenerativeModel('embedding-001')
        
        print("INFO: A.R.I.E.S. Memory Core initialized")
    
    def _init_collections(self):
        """Initialize ChromaDB collections"""
        try:
            # Main knowledge collection
            self.knowledge_collection = self.chroma_client.get_or_create_collection(
                name="aries_knowledge",
                metadata={"description": "Main knowledge base for A.R.I.E.S."}
            )
            
            # Project manifests collection
            self.projects_collection = self.chroma_client.get_or_create_collection(
                name="aries_projects",
                metadata={"description": "Project manifests and state information"}
            )
            
            # Interactions collection
            self.interactions_collection = self.chroma_client.get_or_create_collection(
                name="aries_interactions",
                metadata={"description": "User interaction history"}
            )
            
            # User preferences collection
            self.preferences_collection = self.chroma_client.get_or_create_collection(
                name="aries_preferences",
                metadata={"description": "User preferences and learning"}
            )
            
            print("INFO: ChromaDB collections initialized")
            
        except Exception as e:
            print(f"ERROR: Failed to initialize collections: {e}")
            raise
    
    async def store_interaction(self, query: str, plan: Any, result: Dict, timestamp: float):
        """Store a user interaction for learning"""
        try:
            interaction = Interaction(
                timestamp=timestamp,
                query=query,
                intent_type=plan.intent if hasattr(plan, 'intent') else 'unknown',
                tools_used=plan.tools_required if hasattr(plan, 'tools_required') else [],
                success=len(result.get('steps_failed', [])) == 0,
                user_feedback=None,
                context={
                    "plan": asdict(plan) if hasattr(plan, '__dict__') else str(plan),
                    "result": result
                }
            )
            
            # Store in interactions collection
            self.interactions_collection.add(
                documents=[json.dumps(asdict(interaction))],
                metadatas=[{"type": "interaction", "timestamp": timestamp}],
                ids=[f"interaction_{timestamp}"]
            )
            
            # Update user preferences based on success/failure
            await self._update_preferences_from_interaction(interaction)
            
            print(f"INFO: Interaction stored successfully")
            
        except Exception as e:
            print(f"WARNING: Failed to store interaction: {e}")
    
    async def search_relevant_memories(self, query: str, intent_type: str) -> List[Dict]:
        """Search for relevant memories based on query and intent"""
        try:
            # Get query embedding
            query_embedding = await self._get_embedding(query)
            
            # Search knowledge collection
            knowledge_results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                where={"type": "knowledge"}
            )
            
            # Search interactions collection
            interaction_results = self.interactions_collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                where={"type": "interaction"}
            )
            
            # Combine and format results
            relevant_memories = []
            
            if knowledge_results['documents']:
                for i, doc in enumerate(knowledge_results['documents'][0]):
                    relevant_memories.append({
                        "type": "knowledge",
                        "content": doc,
                        "metadata": knowledge_results['metadatas'][0][i],
                        "relevance_score": knowledge_results['distances'][0][i]
                    })
            
            if interaction_results['documents']:
                for i, doc in enumerate(interaction_results['documents'][0]):
                    relevant_memories.append({
                        "type": "interaction",
                        "content": doc,
                        "metadata": interaction_results['metadatas'][0][i],
                        "relevance_score": interaction_results['distances'][0][i]
                    })
            
            # Sort by relevance
            relevant_memories.sort(key=lambda x: x['relevance_score'])
            
            return relevant_memories[:10]  # Return top 10
            
        except Exception as e:
            print(f"ERROR: Memory search failed: {e}")
            return []
    
    async def get_current_project_context(self) -> Optional[ProjectManifest]:
        """Get the current active project context"""
        try:
            # Look for active project
            results = self.projects_collection.query(
                query_texts=["active project"],
                n_results=1,
                where={"status": "active"}
            )
            
            if results['documents'] and results['documents'][0]:
                project_data = json.loads(results['documents'][0][0])
                return ProjectManifest(**project_data)
            
            return None
            
        except Exception as e:
            print(f"ERROR: Failed to get project context: {e}")
            return None
    
    async def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences for personalization"""
        try:
            results = self.preferences_collection.get(
                where={"type": "preference"}
            )
            
            preferences = {}
            if results['documents']:
                for doc in results['documents']:
                    pref_data = json.loads(doc)
                    category = pref_data['category']
                    if category not in preferences:
                        preferences[category] = []
                    preferences[category].append(pref_data)
            
            return preferences
            
        except Exception as e:
            print(f"ERROR: Failed to get user preferences: {e}")
            return {}
    
    async def store_project_manifest(self, manifest: ProjectManifest) -> bool:
        """Store or update a project manifest"""
        try:
            manifest_data = asdict(manifest)
            
            # Check if project already exists
            existing = self.projects_collection.get(
                where={"name": manifest.name}
            )
            
            if existing['ids']:
                # Update existing project
                self.projects_collection.update(
                    ids=[existing['ids'][0]],
                    documents=[json.dumps(manifest_data)],
                    metadatas=[{"type": "project", "name": manifest.name, "status": manifest.status}]
                )
            else:
                # Add new project
                self.projects_collection.add(
                    documents=[json.dumps(manifest_data)],
                    metadatas=[{"type": "project", "name": manifest.name, "status": manifest.status}],
                    ids=[f"project_{manifest.name}_{datetime.now().timestamp()}"]
                )
            
            print(f"INFO: Project manifest stored for {manifest.name}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to store project manifest: {e}")
            return False
    
    async def store_knowledge(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Store new knowledge in the vector database"""
        try:
            # Get embedding for content
            embedding = await self._get_embedding(content)
            
            # Store in knowledge collection
            self.knowledge_collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[{"type": "knowledge", **metadata}],
                ids=[f"knowledge_{datetime.now().timestamp()}"]
            )
            
            print(f"INFO: Knowledge stored successfully")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to store knowledge: {e}")
            return False
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Gemini"""
        try:
            response = await self.embedding_model.embed_content_async(text)
            return response.embedding
        except Exception as e:
            print(f"ERROR: Failed to get embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 768
    
    async def _update_preferences_from_interaction(self, interaction: Interaction):
        """Update user preferences based on interaction success/failure"""
        try:
            # Analyze interaction for preference learning
            if interaction.success:
                # Successful interaction - reinforce positive preferences
                await self._reinforce_preference("tool_usage", interaction.tools_used[0] if interaction.tools_used else "general", 0.1)
            else:
                # Failed interaction - learn from failure
                await self._reinforce_preference("avoidance", interaction.tools_used[0] if interaction.tools_used else "general", -0.1)
                
        except Exception as e:
            print(f"WARNING: Preference update failed: {e}")
    
    async def _reinforce_preference(self, category: str, preference: str, delta: float):
        """Reinforce or weaken a user preference"""
        try:
            # Get existing preference
            results = self.preferences_collection.get(
                where={"category": category, "preference": preference}
            )
            
            if results['ids']:
                # Update existing preference
                existing_data = json.loads(results['documents'][0])
                new_confidence = max(0.0, min(1.0, existing_data['confidence'] + delta))
                
                self.preferences_collection.update(
                    ids=[results['ids'][0]],
                    documents=[json.dumps({
                        **existing_data,
                        "confidence": new_confidence,
                        "last_updated": datetime.now().isoformat()
                    })]
                )
            else:
                # Create new preference
                new_pref = UserPreference(
                    category=category,
                    preference=preference,
                    confidence=max(0.0, min(1.0, 0.5 + delta)),
                    last_updated=datetime.now().isoformat()
                )
                
                self.preferences_collection.add(
                    documents=[json.dumps(asdict(new_pref))],
                    metadatas=[{"type": "preference", "category": category}],
                    ids=[f"pref_{category}_{preference}_{datetime.now().timestamp()}"]
                )
                
        except Exception as e:
            print(f"WARNING: Preference reinforcement failed: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get Memory Core system status"""
        try:
            return {
                "status": "operational",
                "collections": {
                    "knowledge": self.knowledge_collection.count(),
                    "projects": self.projects_collection.count(),
                    "interactions": self.interactions_collection.count(),
                    "preferences": self.preferences_collection.count()
                },
                "db_path": str(self.db_path),
                "chroma_status": "connected"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to maintain performance"""
        try:
            cutoff_timestamp = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            # Clean old interactions
            old_interactions = self.interactions_collection.get(
                where={"timestamp": {"$lt": cutoff_timestamp}}
            )
            
            if old_interactions['ids']:
                self.interactions_collection.delete(ids=old_interactions['ids'])
                print(f"INFO: Cleaned up {len(old_interactions['ids'])} old interactions")
            
            # Clean old knowledge (keep only high-quality)
            # This is a simplified cleanup - in practice, you'd want more sophisticated logic
            
        except Exception as e:
            print(f"WARNING: Data cleanup failed: {e}")

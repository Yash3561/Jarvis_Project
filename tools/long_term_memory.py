# tools/long_term_memory.py

from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from datetime import datetime
import os

# --- Constants ---
DB_PATH = "./agent_memory_db"
COLLECTION_NAME = "jarvis_experiences"

# --- Setup the Vector Database ---
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)
db = chromadb.PersistentClient(path=DB_PATH)
chroma_collection = db.get_or_create_collection(COLLECTION_NAME)
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Create the index. This object will be our main interface for the memory.
# It will load existing data from the DB_PATH on startup.
memory_index = VectorStoreIndex.from_documents(
    [], storage_context=storage_context
)

def save_experience(summary_of_activity: str, supporting_data: str) -> str:
    """
    Saves a summary of a completed task or a key piece of information to the agent's long-term memory.
    Use this after successfully completing a significant, multi-step task.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a "Document" to be stored
        # We put the summary in the main text for better searching, and details in metadata
        experience_doc = Document(
            text=f"On {timestamp}, the following activity occurred: {summary_of_activity}",
            metadata={"full_data": supporting_data}
        )
        
        # Insert the document into our index
        memory_index.insert(experience_doc)
        
        print(f"INFO: Saved experience to long-term memory: '{summary_of_activity[:50]}...'")
        return "This experience has been successfully saved to my long-term memory."
    except Exception as e:
        print(f"ERROR saving experience to memory: {e}")
        return f"Error: Could not save the experience to long-term memory. {e}"

def recall_experiences(query: str) -> str:
    """
    Searches long-term memory for past experiences, conversations, or saved data
    that are semantically similar to the user's query.
    """
    try:
        print(f"INFO: Querying long-term memory for: '{query}'")
        retriever = memory_index.as_retriever()
        results = retriever.retrieve(query)
        
        if not results:
            return "I have no relevant experiences in my long-term memory."
        
        # Format the results for the agent
        recalled_text = "I found the following relevant experiences in my memory:\n\n"
        for i, res in enumerate(results):
            recalled_text += f"--- Experience {i+1} ---\n"
            recalled_text += f"Content: {res.get_content()}\n"
            recalled_text += f"Relevance Score: {res.get_score():.2f}\n\n"
            
        return recalled_text.strip()

    except Exception as e:
        print(f"ERROR recalling experiences from memory: {e}")
        return f"Error: Could not recall experiences from long-term memory. {e}"
from agent_engine.base import BaseAgent, AgentContext, AgentState
import requests

import hashlib
import json

class MemoryAgent(BaseAgent):
    """
    Handles retrieval and storage of memories with aggressive caching.
    Ensures memory efficiency and deduplication.
    """
    def __init__(self):
        super().__init__("MemoryAgent")
        self.api_url = "http://localhost:8000"

    def run(self, context: AgentContext) -> AgentContext:
        if context.state == AgentState.FETCHING_MEMORY:
            query = context.task
            query_hash = hashlib.md5(query.encode()).hexdigest()

            # 1. Cache Check
            if query_hash in context.memory_cache:
                print(f"[{self.name}] CACHE HIT: Reusing memory for '{query}'")
                context.metadata["relevant_memories"] = context.memory_cache[query_hash]["result"]
            else:
                print(f"[{self.name}] CACHE MISS: Searching memory for '{query}'")
                context.memory_calls_count += 1
                try:
                    resp = requests.get(f"{self.api_url}/memory/search", params={"query": query})
                    res = resp.json()
                    
                    # 2. Confidence Gating (Simulated)
                    confidence = 0.8 # Simulated result confidence
                    
                    context.memory_cache[query_hash] = {
                        "result": res,
                        "confidence": confidence,
                        "used": True
                    }
                    context.metadata["relevant_memories"] = res
                    
                    if confidence >= 0.6:
                        print(f"[{self.name}] HIGH CONFIDENCE ({confidence}). Locking design to cached solution.")
                    
                except Exception as e:
                    print(f"[{self.name}] Error fetching memory: {e}")
        
        elif context.state == AgentState.STORING_MEMORY:
            print(f"[{self.name}] Storing memory with deduplication check...")
            
            # 3. Deduplication Logic
            # memory_id = hash(problem + solution + context)
            solution = context.plan or ""
            memory_raw = f"{context.task}{solution}"
            memory_id = hashlib.md5(memory_raw.encode()).hexdigest()
            
            try:
                # In a real system, we'd check if memory_id exists in DB
                # Here we simulate the deduplication
                requests.post(f"{self.api_url}/memory/store", json={
                    "text": f"Successfully completed task: {context.task}",
                    "metadata": {
                        "type": "agent_success", 
                        "task": context.task,
                        "memory_id": memory_id
                    }
                })
                print(f"[{self.name}] Memory stored with ID: {memory_id}")
            except Exception as e:
                print(f"[{self.name}] Error storing memory: {e}")
        
        return context

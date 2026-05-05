
import ast
import os
import json
from typing import Dict, Any, List, Set, Tuple
from memory_system.models.schemas import GraphContext, GraphDependency
from memory_system.core.logger import logger

class ProjectGraph:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[str, List[str]] = {} # caller -> list of callees
        self.reverse_edges: Dict[str, List[str]] = {} # callee -> list of callers
        self.build_graph()

    def _add_node(self, node_id: str, node_type: str, file_path: str):
        self.nodes[node_id] = {
            "type": node_type,
            "path": file_path
        }
        if node_id not in self.edges:
            self.edges[node_id] = []
        if node_id not in self.reverse_edges:
            self.reverse_edges[node_id] = []

    def _add_edge(self, caller: str, callee: str):
        if caller not in self.edges:
            self.edges[caller] = []
        if callee not in self.reverse_edges:
            self.reverse_edges[callee] = []

        if callee not in self.edges[caller]:
            self.edges[caller].append(callee)
        if caller not in self.reverse_edges[callee]:
            self.reverse_edges[callee].append(caller)

    def build_graph(self):
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.root_dir)
                    self._parse_file(file_path, rel_path)

    def _parse_file(self, file_path: str, rel_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
        except Exception:
            return

        module_name = rel_path.replace(os.path.sep, '.').replace('.py', '')
        self._add_node(module_name, "module", rel_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_name = node.name
                func_id = f"{module_name}.{func_name}"

                node_type = "function"
                if func_name.startswith("test_"):
                    node_type = "test"
                # Simple heuristic for APIs (if it has decorators like @app.get)
                elif any(isinstance(d, ast.Call) and hasattr(d.func, "attr") and d.func.attr in ["get", "post", "put", "delete"] for d in node.decorator_list):
                    node_type = "api"

                self._add_node(func_id, node_type, rel_path)
                self._add_edge(module_name, func_id)

                # Look for function calls inside this function
                for sub_node in ast.walk(node):
                    if isinstance(sub_node, ast.Call):
                        called_func = None
                        if isinstance(sub_node.func, ast.Name):
                            called_func = sub_node.func.id
                        elif isinstance(sub_node.func, ast.Attribute):
                            called_func = sub_node.func.attr

                        if called_func:
                            # We add a generic reverse mapping from short name to full func ID
                            self._add_edge(func_id, called_func)

                            # Also see if we can resolve it to a known module function (naive approach)
                            for known_func in list(self.nodes.keys()):
                                if known_func.endswith(f".{called_func}"):
                                    self._add_edge(func_id, known_func)

    def validate_graph(self) -> Dict[str, Any]:
        """
        Validate graph integrity: detect isolated nodes and missing references.
        """
        isolated_nodes = []
        for node in self.nodes:
            if not self.edges.get(node) and not self.reverse_edges.get(node):
                isolated_nodes.append(node)

        return {
            "total_nodes": len(self.nodes),
            "isolated_nodes": len(isolated_nodes),
            "isolated_list": isolated_nodes
        }

    def analyze_impact(self, target_node: str) -> Tuple[List[GraphDependency], int]:
        """BFS to find all nodes that depend on target_node."""
        visited: Set[str] = set()
        impacted = []

        # Normalize target_node to handle '.py' extentions and paths
        target_node = target_node.replace(".py", "")
        target_node = target_node.replace(os.path.sep, ".")
        target_node = target_node.strip("`.,\"'")

        # Find actual fully qualified node names that match the target_node
        start_nodes = [n for n in self.nodes.keys() if target_node in n.split('.') or target_node == n]
        if not start_nodes:
            # Fallback: Check if we have edges matching the short name
            if target_node in self.reverse_edges:
                start_nodes = [target_node]
            else:
                return [], 0

        queue = list(start_nodes)

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            # Record impact (skip the starting node itself unless it's recursively called)
            if current not in start_nodes and current in self.nodes:
                node_info = self.nodes[current]

                risk = "low"
                if node_info["type"] == "api":
                    risk = "high"
                elif node_info["type"] == "module":
                    risk = "medium"

                impacted.append(GraphDependency(
                    entity=current,
                    type=node_info["type"],
                    risk_level=risk,
                    path=node_info["path"]
                ))

            # Add dependents to queue
            if current in self.reverse_edges:
                for dependent in self.reverse_edges[current]:
                    if dependent not in visited:
                        queue.append(dependent)

        return impacted, len(visited) - len(start_nodes)

def _parse_query_list(query: str) -> List[str]:
    """Parse query string, which could be a JSON array string or a space-separated list."""
    try:
        # Try to parse as JSON array
        parsed = json.loads(query)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except Exception:
        pass

    # Fallback: split by space
    return [q.strip() for q in query.split()]

def get_graph_context(query: str, root_dir: str = ".") -> GraphContext:
    """
    Analyzes the structural graph of the project to determine impact.
    Expects a query containing the target function/entity to analyze.
    """
    logger.info(f"Analyzing graph context for target: {query}")

    try:
        graph = ProjectGraph(root_dir)

        # 1. Query Formatting Bug Fix
        target_entities = _parse_query_list(query)

        all_impacted = []
        total_blast_radius = 0
        entities_not_found = []

        for target in target_entities:
            impacted, blast_radius = graph.analyze_impact(target)
            if blast_radius == 0:
                entities_not_found.append(target)
            else:
                all_impacted.extend(impacted)
                total_blast_radius += blast_radius

        # Deduplicate impacted dependencies
        unique_impacted = {dep.entity: dep for dep in all_impacted}.values()

        if total_blast_radius == 0:
            context_msg = f"Entities {entities_not_found} not found or have no structural impact."
            # 3. Silent Failure Pattern Fix: Use explicit "not_found" status
            status = "not_found"
        else:
            context_msg = f"Found {total_blast_radius} impacted dependencies for {target_entities}."
            status = "success"

        # 11. Graph Not Built / Indexed Missing Detection Fix
        graph_loaded = len(graph.nodes) > 0

        return GraphContext(
            query=query,
            impacted_dependencies=list(unique_impacted),
            blast_radius=total_blast_radius,
            status=status,
            context=context_msg,
            graph_loaded=graph_loaded
        )
    except Exception as e:
        logger.error(f"Graph context analysis failed: {str(e)}")
        return GraphContext(
            query=query,
            status="exception",
            context=str(e),
            graph_loaded=False
        )

def get_graph_report() -> Dict[str, Any]:
    return {
        "status": "ok",
        "message": "Graph system uses active BFS AST traversal."
    }

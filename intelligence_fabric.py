"""
VAIXLNS Intelligence Fabric
A DAG-based cognitive architecture that dynamically composes capabilities
based on task analysis, executes them with parallelization awareness,
and learns from outcomes.

Core Innovation:
- Dynamic DAG construction instead of linear pipelines
- Capability composition based on real-time analysis
- Parallel execution where dependencies allow
- Integrated feedback loop for continuous improvement
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Set, Tuple, Any
from enum import Enum
import json
from collections import defaultdict
import time


class CapabilityType(Enum):
    """Classification of capability roles within the fabric"""
    ANALYZER = "analyzer"          # Understands the task
    PLANNER = "planner"            # Structures the approach
    EXECUTOR = "executor"          # Performs the work
    VALIDATOR = "validator"        # Checks quality
    OPTIMIZER = "optimizer"        # Improves results
    LEARNER = "learner"           # Updates knowledge


@dataclass
class Capability:
    """A composable intelligence unit"""
    name: str
    capability_type: CapabilityType
    score: Callable[[dict], float]           # Task -> confidence score
    execute: Callable[[dict], dict]          # Task -> result
    dependencies: List[str] = field(default_factory=list)  # Required capabilities
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Node:
    """DAG Node representing a capability in execution context"""
    id: str
    capability: Capability
    dependencies: Set[str] = field(default_factory=set)
    status: str = "pending"  # pending, executing, completed, failed
    result: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0


class CapabilityGraph:
    """Directed Acyclic Graph of capabilities with dependency resolution"""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Set[str]] = defaultdict(set)
    
    def add_node(self, node: Node):
        """Add a capability node to the graph"""
        self.nodes[node.id] = node
        for dep in node.dependencies:
            self.edges[dep].add(node.id)
    
    def topological_sort(self) -> List[str]:
        """Returns capabilities in dependency order"""
        visited = set()
        temp_visited = set()
        order = []
        
        def dfs(node_id):
            if node_id in temp_visited:
                raise ValueError(f"Circular dependency detected at {node_id}")
            if node_id in visited:
                return
            
            temp_visited.add(node_id)
            for neighbor in self.edges.get(node_id, []):
                dfs(neighbor)
            temp_visited.remove(node_id)
            visited.add(node_id)
            order.append(node_id)
        
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id)
        
        return order
    
    def get_parallel_layers(self) -> List[List[str]]:
        """Group nodes into layers that can execute in parallel"""
        in_degree = {node_id: len(self.nodes[node_id].dependencies) 
                     for node_id in self.nodes}
        layers = []
        
        remaining = set(self.nodes.keys())
        while remaining:
            current_layer = [n for n in remaining if in_degree[n] == 0]
            if not current_layer:
                raise ValueError("Circular dependency detected")
            
            layers.append(current_layer)
            for node_id in current_layer:
                remaining.remove(node_id)
                for dependent in self.edges.get(node_id, []):
                    in_degree[dependent] -= 1
        
        return layers
    
    def optimize(self) -> 'CapabilityGraph':
        """Optimize the graph: remove redundant nodes, merge compatible capabilities"""
        # Placeholder for optimization logic
        # Could include: node merging, unused capability removal, caching strategies
        return self


class IntelligenceFabric:
    """
    DAG-based cognitive architecture.
    Analyzes tasks, builds capability graphs, executes with dependency awareness,
    and learns from outcomes.
    """
    
    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.knowledge_base: Dict[str, Any] = {}
    
    def register(self, capability: Capability):
        """Register a capability in the fabric"""
        self.capabilities[capability.name] = capability
    
    def analyze(self, task: dict) -> dict:
        """
        Analyze task to understand its nature, complexity, and requirements.
        Returns metadata used for graph construction.
        """
        analysis = {
            "task_type": task.get("type", "unknown"),
            "complexity": self._estimate_complexity(task),
            "required_capabilities": self._identify_required_capabilities(task),
            "parallelizable": task.get("parallelizable", True),
            "quality_threshold": task.get("quality_threshold", 0.8),
        }
        return analysis
    
    def build_capability_graph(self, task: dict, analysis: dict) -> CapabilityGraph:
        """
        Build a DAG of capabilities needed for this task.
        Graph construction based on:
        - Task analysis
        - Capability scores for this task type
        - Known dependencies
        """
        graph = CapabilityGraph()
        
        # Score all capabilities for this task
        scored_capabilities = [
            (name, cap, cap.score(task))
            for name, cap in self.capabilities.items()
        ]
        
        # Filter by relevance threshold
        relevant = [
            (name, cap) for name, cap, score in scored_capabilities
            if score > 0.3
        ]
        
        # Create nodes
        for name, cap in relevant:
            node = Node(
                id=name,
                capability=cap,
                dependencies=set(cap.dependencies)
            )
            graph.add_node(node)
        
        return graph
    
    def optimize(self, graph: CapabilityGraph) -> CapabilityGraph:
        """
        Optimize the graph:
        - Remove redundant capabilities
        - Identify parallelizable branches
        - Merge compatible capabilities
        - Apply caching strategies
        """
        return graph.optimize()
    
    def execute_graph(self, graph: CapabilityGraph, task: dict) -> dict:
        """
        Execute the capability graph respecting dependencies.
        Executes capabilities in parallel where possible.
        """
        layers = graph.get_parallel_layers()
        results = {}
        
        for layer_idx, layer in enumerate(layers):
            layer_results = {}
            
            # Execute all capabilities in layer (simulated parallelism)
            for node_id in layer:
                node = graph.nodes[node_id]
                capability = node.capability
                
                # Prepare execution context with results from dependencies
                context = {
                    "task": task,
                    "dependencies": {
                        dep: results.get(dep, {})
                        for dep in node.dependencies
                    }
                }
                
                # Execute capability
                start_time = time.time()
                try:
                    result = capability.execute(context)
                    node.status = "completed"
                    node.result = result
                    node.execution_time = time.time() - start_time
                    layer_results[node_id] = result
                except Exception as e:
                    node.status = "failed"
                    node.result = {"error": str(e)}
                    layer_results[node_id] = {"error": str(e)}
            
            results.update(layer_results)
        
        return results
    
    def evaluate(self, task: dict, results: dict) -> dict:
        """
        Evaluate the quality of results against task requirements.
        Returns a quality report.
        """
        report = {
            "task_type": task.get("type"),
            "num_capabilities_executed": len(results),
            "all_succeeded": all("error" not in r for r in results.values()),
            "quality_score": self._compute_quality_score(results),
            "timestamp": time.time(),
        }
        return report
    
    def learn(self, report: dict):
        """
        Update knowledge base from execution outcomes.
        Learns which capability combinations work best for different task types.
        """
        self.execution_history.append(report)
        
        # Update statistics
        task_type = report.get("task_type", "unknown")
        if task_type not in self.knowledge_base:
            self.knowledge_base[task_type] = {
                "success_count": 0,
                "failure_count": 0,
                "avg_quality": 0.0,
            }
        
        if report.get("all_succeeded"):
            self.knowledge_base[task_type]["success_count"] += 1
            quality = report.get("quality_score", 0.0)
            kb = self.knowledge_base[task_type]
            total = kb["success_count"] + kb["failure_count"]
            kb["avg_quality"] = (kb["avg_quality"] * (total - 1) + quality) / total
        else:
            self.knowledge_base[task_type]["failure_count"] += 1
    
    def think(self, task: dict) -> dict:
        """
        Main cognitive loop:
        1. Analyze the task
        2. Build capability graph
        3. Optimize the graph
        4. Execute with dependency awareness
        5. Evaluate results
        6. Update knowledge
        """
        # Step 1: Analyze
        analysis = self.analyze(task)
        
        # Step 2: Build graph
        graph = self.build_capability_graph(task, analysis)
        
        # Step 3: Optimize
        optimized_graph = self.optimize(graph)
        
        # Step 4: Execute
        results = self.execute_graph(optimized_graph, task)
        
        # Step 5: Evaluate
        report = self.evaluate(task, results)
        
        # Step 6: Learn
        self.learn(report)
        
        return {
            "task": task,
            "analysis": analysis,
            "results": results,
            "report": report,
            "execution_layers": len(optimized_graph.get_parallel_layers()),
        }
    
    # Helper methods
    def _estimate_complexity(self, task: dict) -> float:
        """Estimate task complexity (0.0 to 1.0)"""
        return task.get("complexity", 0.5)
    
    def _identify_required_capabilities(self, task: dict) -> List[str]:
        """Identify which capability types are needed"""
        task_type = task.get("type", "unknown")
        mapping = {
            "analysis": ["analyzer"],
            "planning": ["analyzer", "planner"],
            "coding": ["analyzer", "planner", "executor", "validator"],
            "optimization": ["analyzer", "optimizer", "validator"],
        }
        return mapping.get(task_type, ["analyzer"])
    
    def _compute_quality_score(self, results: dict) -> float:
        """Compute overall quality score from results"""
        if not results:
            return 0.0
        
        scores = []
        for result in results.values():
            if "error" not in result:
                scores.append(result.get("quality", 0.8))
        
        return sum(scores) / len(scores) if scores else 0.0


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Create fabric
    fabric = IntelligenceFabric()
    
    # Register capabilities
    fabric.register(Capability(
        name="TaskAnalyzer",
        capability_type=CapabilityType.ANALYZER,
        score=lambda t: 0.99 if t["type"] in ["coding", "planning"] else 0.6,
        execute=lambda ctx: {"analysis": "task understood", "quality": 0.95},
        dependencies=[]
    ))
    
    fabric.register(Capability(
        name="ArchitecturePlanner",
        capability_type=CapabilityType.PLANNER,
        score=lambda t: 0.95 if t["type"] == "coding" else 0.3,
        execute=lambda ctx: {"plan": "architecture designed", "quality": 0.93},
        dependencies=["TaskAnalyzer"]
    ))
    
    fabric.register(Capability(
        name="CodeGenerator",
        capability_type=CapabilityType.EXECUTOR,
        score=lambda t: 0.97 if t["type"] == "coding" else 0.1,
        execute=lambda ctx: {"code": "generated", "quality": 0.91},
        dependencies=["ArchitecturePlanner"]
    ))
    
    fabric.register(Capability(
        name="CodeValidator",
        capability_type=CapabilityType.VALIDATOR,
        score=lambda t: 0.88 if t["type"] == "coding" else 0.2,
        execute=lambda ctx: {"validated": True, "quality": 0.89},
        dependencies=["CodeGenerator"]
    ))
    
    fabric.register(Capability(
        name="PerformanceOptimizer",
        capability_type=CapabilityType.OPTIMIZER,
        score=lambda t: 0.85 if t.get("optimize", False) else 0.2,
        execute=lambda ctx: {"optimized": True, "quality": 0.87},
        dependencies=["CodeValidator"]
    ))
    
    # Test task
    task = {
        "type": "coding",
        "goal": "build runtime",
        "optimize": True,
        "complexity": 0.7,
    }
    
    # Run cognitive loop
    print("\n" + "="*70)
    print("VAIXLNS Intelligence Fabric - DAG-based Cognitive Architecture")
    print("="*70)
    
    result = fabric.think(task)
    
    print(f"\n📋 Task: {result['task']}")
    print(f"\n🧠 Analysis: {json.dumps(result['analysis'], indent=2)}")
    print(f"\n📊 Execution Layers (parallelizable groups): {result['execution_layers']}")
    print(f"\n✅ Results:")
    for cap_name, cap_result in result['results'].items():
        print(f"   {cap_name}: {cap_result}")
    print(f"\n📈 Report: {json.dumps(result['report'], indent=2)}")
    print(f"\n🧠 Knowledge Base: {json.dumps(fabric.knowledge_base, indent=2)}")
    print("="*70 + "\n")

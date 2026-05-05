# ECAE Base Rules

## Objective
Enforce the prediction, filtering, and execution pipeline explicitly.

## Flow Requirements
1. **Predict:** Agent queries semantic history (`search_memory`).
2. **Filter:** Agent maps structural blast radius (`get_graph_context`).
3. **Optimize:** Agent produces branching candidate paths.
4. **Generate:** Code is synthesized.
5. **Execute:** Run inside ephemeral container. Truth evaluates.
6. **Learn:** Success or failure state is immediately embedded and stored to Qdrant memory layer.

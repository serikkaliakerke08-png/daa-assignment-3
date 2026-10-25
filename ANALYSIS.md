# Assignment 3: Graph Algorithms

Language: Python 3.12+. No external dependencies. Entry point: `src/Python/main.py`.

## Commands

Run from the repository root:

```sh
python tools/run.py --setup
python tools/run.py --check
python tests/test_solution.py
python tests/benchmark.py
python tools/run.py --input tests/my_cases.jsonl
```

Python needs no compilation. Setup passed; all 36 public cases and the repeated-batch state-reset check passed. Own tests passed. Actual evidence is in `tests/setup_results.txt`, `tests/public_results.txt`, `tests/test_results.txt`, `tests/actual.jsonl`, and `tests/routes.json`.

## DSU

Initialize one root and size 1 per vertex. Find uses path halving (path compression); union attaches the smaller root below the larger root. After each operation, append component count and largest size.

Invariant: each tree represents exactly one connected component, root sizes count its vertices, and components counts roots. Joining different roots merges exactly two components, decreasing the count by one and updating the largest size. Repeated and self unions change nothing. Compression preserves the root and therefore the represented partition. Empty input returns no states and uses largest 0.

Time: O(n + q alpha(n)) amortized. Memory: O(n+q), including returned states.

## Kruskal

Sort original edge IDs by weight. Accept an edge exactly when DSU joins different roots; add its weight and original ID.

Invariant: selected edges form an acyclic forest extendible to an optimal spanning forest. For an accepted edge, consider the cut separating its current DSU component from the rest. Any lighter crossing edge would already have been considered and would have joined these components; thus the accepted edge is a minimum crossing choice. The cut exchange property preserves an optimal extension. Rejected edges close cycles. At the end each input component is spanned, and DSU counts components including isolates. Negative weights and ties do not affect the cut argument. Loops are rejected, parallel IDs remain distinct, and Python integers prevent overflow.

Time: O(n + m log(m+1)); union work is dominated by this bound. Memory: O(n+m), including sorted IDs and result. Empty graphs return cost 0 and components 0.

## Prim

Build an undirected adjacency list containing weights, original IDs and opposite vertices. Start from every still-unvisited root. A lazy min-heap stores crossing candidates. Pop the lightest candidate, discard it if its endpoint is already visited, otherwise select it and add its outgoing candidates.

Invariant: the visited portion of the current component is connected and selected edges can be extended to an optimum. Every edge from that portion to an unvisited vertex has a heap candidate. After stale entries are removed, the next edge is a minimum cut edge, so the cut exchange property proves it safe. Each selected edge discovers one vertex and cannot create a cycle. An empty heap completes one component; restarting counts disconnected components and isolates. Loops lead to already visited vertices and cannot be selected. Ties, parallel edges and negative weights are handled by the same rule.

Time: O(n + m log(m+1)) with the lazy heap. Memory: O(n+m). Empty graphs return an empty forest.

## Kosaraju SCC

Build the graph and transpose. First DFS records finish order. Process vertices in decreasing finish order in a second DFS on the transpose; each new traversal receives a new label. Scan original edges and deduplicate cross-label pairs with a set.

First-pass stack frames store the next neighbor index, so a vertex finishes only after all descendants. For an edge between different SCCs, the source SCC has larger maximum finish time than the target SCC. Consequently, the next unassigned SCC in decreasing finish order cannot escape to another unassigned SCC in the transpose. All vertices inside it are mutually reachable, so the second pass finds exactly that SCC. Repeating partitions all vertices. The final scan includes every cross-component pair once and excludes internal edges. Isolates receive separate labels; loops and duplicates cause no problem.

Time: O(n+m) expected with hash-set deduplication. Memory: O(n+m). Empty input yields two empty arrays. Condensation output order need not be sorted.

## DFS topological ordering

`dfs_order` uses white/unvisited, gray/active and black/finished states. Each explicit frame retains a vertex and its next neighbor index. An edge to gray finds a directed cycle; return no order. Otherwise reverse finish order after visiting every component.

Invariant: gray vertices are exactly the current DFS path. An edge to a gray ancestor closes a cycle. Conversely a directed cycle cannot finish without an edge to an active vertex. In an acyclic graph every edge u->v has v finished before u, whether v was reached recursively or already finished. Reversing finish order therefore places u before v. Every vertex is started and finished once. Duplicate edges are harmless; self-loops and disconnected cycles are rejected. The empty graph is acyclic.

Time and memory: O(n+m). Resuming saved neighbor positions avoids repeated scans.

## DAG shortest paths and route helper

First use three-state DFS on the whole graph. Any cycle, even unreachable from the source, returns false and empty arrays. Initialize only the source distance to 0; all others are None. Traverse topological order and relax outgoing edges only from reachable vertices. Store the original edge ID whenever a strictly shorter distance is found.

Invariant: when a vertex is processed, its finite distance is optimal. All possible predecessors already occur earlier in topological order. Induction over that order proves that considering their final distances finds the best possible last edge. Negative weights are safe because there are no cycles. Unreachable predecessors never produce artificial routes. Each stored parent ends at its vertex and points backward in topological order; following parents must terminate at the source. Strict comparison preserves the first discovered witness on ties. Source parent stays -1 because no reachable path can return to the source in a DAG.

Time and memory: O(n+m). `reconstruct_route(source, target, edges, parent_edge)` assumes a valid acyclic result, follows incoming IDs backward and reverses the vertex list. Unreachable targets return []; source returns [source]. Time and output space are O(L), where L is the route length; it does not copy or scan the entire graph. Do not call it on the empty arrays of a cyclic result.

Actual calls in `tests/test_solution.py` use source 0 and edges:

```text
0: [0,1,2]
1: [0,1,2]
2: [1,2,-3]
3: [2,3,1]
4: [0,3,0]
```

Distances are [0,2,-1,0,null]; selected parent IDs are [-1,0,2,4,-1].

| Target | Helper result | Edge IDs | Cost |
|---|---|---|---|
| 3 | [0,3] | [4] | 0 |
| 0 | [0] | [] | 0 |
| 4 | [] | [] | unreachable |
| 1 | [0,1] | [0] | 2 |

The test checks edge direction and summed weight. The tied route [0,1,2,3] also costs 0; the implementation keeps the direct route, discovered first. Parallel ID 1 is also a valid parent for vertex 1. Semantic checks accept that alternative and reject ID 2 as a parent of vertex 1 because it ends at vertex 2.

## State reset, scale and own test justification

There is no mutable global algorithm state. Each request allocates fresh DSU, adjacency, traversal, heap and result arrays. The unchanged adapter preserves ping and outputs one JSON result per input line. Iterative DFS handles depth 100000 without changing Python's recursion limit.

`tests/expected.json` contains own inputs and expected contract fields. `my_cases.jsonl` contains their JSON Lines inputs. `actual.jsonl` records three repeated mixed batches in one process. Expected values are justified as follows:

- DSU: self/repeated unions preserve counts; disjoint pairs produce two size-2 groups; the last union forms one size-4 group.
- Empty inputs have no edges, states or SCCs; topological order exists.
- Small weighted multigraph: an independent exhaustive subset enumerator using sets checks the optimum. One weight -2 and one weight 4 connect three vertices, with a fourth isolate; a negative loop cannot belong to a forest. The 4-edge chain costs 4000000000.
- SCC: 0 and 1 reach each other, vertex 2 has no return path, and 3 and 4 reach each other. Only the consecutive cross-group pairs belong to condensation.
- Topological cases: two independent roots precede 2 then 3; the disconnected 2<->3 cycle makes an ordering impossible.
- DAG: the disconnected cycle must be rejected. For the route graph, enumerate the paths to get 0, 2, -1, 0 and unreachable.

Semantic witness checks accept distinct tied forests, distinct topological orders, renamed SCC labels and alternative shortest-path parents. They reject duplicate forest IDs, reversed precedence, missing condensation and a wrongly directed parent. The supplied public validator is reused for contract checking; the tiny-forest optimum is computed independently.

The scale generator in `test_solution.py` runs every method with n=100000 and q or m=250000. DSU's repeated chain joins all vertices. Forest inputs use a negative chain plus loops, forcing exactly the chain and cost -99999000000000. Directed inputs use the same forward chain plus repeated forward edges, giving 100000 singleton SCCs, ascending topological order and the same final negative distance. The reconstructed full chain has 100000 vertices. Large inputs are generated rather than stored; commands and generation code are included.

## Benchmark protocol and measured results

Run `python tests/benchmark.py`. Each graph is generated once and shared by both methods: a chain ensuring connectivity, followed by random edges until m=5n. Weights are uniformly sampled integers from -1000 to 1000. Python `random.Random(2537+n)` supplies deterministic generation. Self-loops and parallel edges are allowed. Before timing, compare costs and component counts and validate each forest. Each method has one untimed warm-up call per size. Three measured calls follow, alternating which method runs first. Timer: time.perf_counter. Boundary: complete algorithm call, including internal adjacency/DSU initialization and sorting or heap operations, excluding generation, JSON parsing, validation, output and compilation. Both methods receive the same request object and do not modify it. Normal Python garbage collection remains enabled. Timings are seconds.

Environment: 3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]; Linux-6.18.55-x86_64-with-glibc2.39; AMD EPYC 9V74 80-Core Processor. Shared container, no dedicated CPU guarantee.

| n | m | seed | Kruskal: 3 times | median | Prim: 3 times | median |
|---|---|---|---|---|---|---|
| 1000 | 5000 | 3537 | 0.002552, 0.003581, 0.002954 | 0.002954 | 0.005045, 0.004214, 0.005071 | 0.005045 |
| 10000 | 50000 | 12537 | 0.050056, 0.048742, 0.048329 | 0.048742 | 0.106216, 0.114744, 0.111834 | 0.111834 |
| 50000 | 250000 | 52537 | 0.391903, 0.375004, 0.383318 | 0.383318 | 0.985154, 0.983345, 0.997845 | 0.985154 |

Kruskal was faster at all three sizes in this run. Python sorting and DSU were cheaper here than building adjacency lists and managing lazy heap entries. Both methods have the same stated asymptotic upper bound for this implementation. Three timings on one sparse graph family do not establish a universal ranking; density, graph structure, runtime and shared CPU load can change the result. Full precision values and verified costs are in tests/benchmark_results.json.

## Sources and AI disclosure

The assignment template, specification, JSON adapter, public cases and public semantic validator are from [https://github.com/RZhaniya/daa-assignment-3-graphs](https://github.com/RZhaniya/daa-assignment-3-graphs) (see original README and tools).Verification performed in the execution environment: setup, all 36 public cases, repeated mixed requests, own semantic and route checks, full-limit tests and the recorded benchmark.

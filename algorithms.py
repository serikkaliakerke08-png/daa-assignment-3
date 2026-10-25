"""Graph algorithms. All traversal state belongs to the current request."""
import heapq


class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        self.largest = 1 if n else 0

    def find(self, v):
        while v != self.parent[v]:
            self.parent[v] = self.parent[self.parent[v]]
            v = self.parent[v]
        return v

    def union(self, u, v):
        u, v = self.find(u), self.find(v)
        if u == v:
            return False
        if self.size[u] < self.size[v]:
            u, v = v, u
        self.parent[v] = u
        self.size[u] += self.size[v]
        self.components -= 1
        self.largest = max(self.largest, self.size[u])
        return True


def dsu(request):
    sets = DSU(request['n'])
    states = []
    for u, v in request['operations']:
        sets.union(u, v)
        states.append([sets.components, sets.largest])
    return {'states': states}


def kruskal(request):
    edges = request['edges']
    sets = DSU(request['n'])
    cost, chosen = 0, []
    for i in sorted(range(len(edges)), key=lambda i: edges[i][2]):
        u, v, w = edges[i]
        if sets.union(u, v):
            chosen.append(i)
            cost += w
    return {'cost': cost, 'edge_ids': chosen, 'components': sets.components}


def prim(request):
    n, edges = request['n'], request['edges']
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        adj[u].append((w, i, v))
        adj[v].append((w, i, u))
    seen = [False] * n
    cost, components, chosen = 0, 0, []
    for root in range(n):
        if seen[root]:
            continue
        components += 1
        seen[root] = True
        heap = []
        for item in adj[root]:
            if not seen[item[2]]:
                heapq.heappush(heap, item)
        while heap:
            w, i, v = heapq.heappop(heap)
            if seen[v]:
                continue
            seen[v] = True
            chosen.append(i)
            cost += w
            for item in adj[v]:
                if not seen[item[2]]:
                    heapq.heappush(heap, item)
    return {'cost': cost, 'edge_ids': chosen, 'components': components}


def dfs_order(adj):
    """Return reverse finish order, or None on an active-vertex edge."""
    color = [0] * len(adj)
    finish = []
    for root in range(len(adj)):
        if color[root]:
            continue
        color[root] = 1
        stack = [(root, 0)]
        while stack:
            u, index = stack[-1]
            if index == len(adj[u]):
                stack.pop()
                color[u] = 2
                finish.append(u)
                continue
            v = adj[u][index]
            stack[-1] = (u, index + 1)
            if color[v] == 1:
                return None
            if color[v] == 0:
                color[v] = 1
                stack.append((v, 0))
    finish.reverse()
    return finish


def scc(request):
    n, edges = request['n'], request['edges']
    adj = [[] for _ in range(n)]
    rev = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        rev[v].append(u)
    seen, finish = [False] * n, []
    for root in range(n):
        if seen[root]:
            continue
        seen[root] = True
        stack = [(root, 0)]
        while stack:
            u, index = stack[-1]
            if index == len(adj[u]):
                stack.pop()
                finish.append(u)
            else:
                v = adj[u][index]
                stack[-1] = (u, index + 1)
                if not seen[v]:
                    seen[v] = True
                    stack.append((v, 0))
    labels = [-1] * n
    label = 0
    for root in reversed(finish):
        if labels[root] != -1:
            continue
        labels[root] = label
        stack = [root]
        while stack:
            u = stack.pop()
            for v in rev[u]:
                if labels[v] == -1:
                    labels[v] = label
                    stack.append(v)
        label += 1
    pairs = {(labels[u], labels[v]) for u, v in edges if labels[u] != labels[v]}
    return {'component': labels, 'condensation': [list(p) for p in pairs]}


def topo(request):
    adj = [[] for _ in range(request['n'])]
    for u, v in request['edges']:
        adj[u].append(v)
    order = dfs_order(adj)
    return {'acyclic': order is not None, 'order': [] if order is None else order}


def dag(request):
    n, edges, source = request['n'], request['edges'], request['source']
    adj = [[] for _ in range(n)]
    outgoing = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        adj[u].append(v)
        outgoing[u].append((v, w, i))
    order = dfs_order(adj)
    if order is None:
        return {'acyclic': False, 'distance': [], 'parent_edge': []}
    distance, parent = [None] * n, [-1] * n
    distance[source] = 0
    for u in order:
        if distance[u] is None:
            continue
        for v, w, i in outgoing[u]:
            candidate = distance[u] + w
            if distance[v] is None or candidate < distance[v]:
                distance[v] = candidate
                parent[v] = i
    return {'acyclic': True, 'distance': distance, 'parent_edge': parent}


def reconstruct_route(source, target, edges, parent_edge):
    """For a valid DAG result, return vertices; [] means unreachable."""
    route = []
    v = target
    while v != source:
        i = parent_edge[v]
        if i == -1:
            return []
        route.append(v)
        v = edges[i][0]
    route.append(source)
    route.reverse()
    return route

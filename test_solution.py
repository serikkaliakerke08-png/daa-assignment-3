"""Own cases, semantic witnesses, route calls, full-limit generators."""
import itertools
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src/Python'), str(ROOT / 'tools')]
import algorithms as a
from public_validate import check


def brute_forest(n, edges):
    # Independent connectivity with sets, then exhaustive subsets on tiny inputs.
    groups = [{i} for i in range(n)]
    for u, v, _ in edges:
        x = next(g for g in groups if u in g)
        y = next(g for g in groups if v in g)
        if x is not y:
            x.update(y)
            groups.remove(y)
    c = len(groups)
    best = None
    for ids in itertools.combinations(range(len(edges)), n-c):
        reached = [{i} for i in range(n)]
        valid = True
        for i in ids:
            u, v, w = edges[i]
            x = next(g for g in reached if u in g)
            y = next(g for g in reached if v in g)
            if x is y:
                valid = False
                break
            x.update(y)
            reached.remove(y)
        if valid:
            cost = sum(edges[i][2] for i in ids)
            best = cost if best is None else min(best, cost)
    return {'cost': best, 'components': c}


def main():
    cases = []
    def add(task, n, expected, **kwargs):
        cases.append({'input': dict(task=task, n=n, **kwargs), 'output': expected})
    add('dsu', 4, {'states': [[4,1],[3,2],[3,2],[2,2],[1,4]]},
        operations=[[0,0],[0,1],[1,0],[2,3],[1,3]])
    for task in ('dsu','kruskal','prim','scc','topo'):
        expected = {'dsu': {'states': []}, 'kruskal': {'cost':0,'components':0},
                    'prim': {'cost':0,'components':0}, 'scc': {'component':[]},
                    'topo': {'acyclic':True}}[task]
        add(task, 0, expected, **({'operations':[]} if task=='dsu' else {'edges':[]}))
    edges = [[0,1,-2],[0,1,-2],[1,2,4],[0,2,4],[2,2,-100]]
    for task in ('kruskal','prim'):
        add(task, 4, brute_forest(4,edges), edges=edges)
        add(task, 5, {'cost':4000000000,'components':1},
            edges=[[i,i+1,1000000000] for i in range(4)])
    add('scc', 5, {'component':[0,0,1,2,2]},
        edges=[[0,1],[1,0],[1,2],[0,2],[2,3],[3,4],[4,3],[4,4]])
    add('topo', 4, {'acyclic':True}, edges=[[0,2],[1,2],[2,3],[0,2]])
    add('topo', 4, {'acyclic':False}, edges=[[0,1],[2,3],[3,2]])
    add('dag', 4, {'acyclic':False}, source=0, edges=[[0,1,2],[2,3,1],[3,2,-1]])
    add('dag', 5, {'acyclic':True,'distance':[0,2,-1,0,None]}, source=0,
        edges=[[0,1,2],[0,1,2],[1,2,-3],[2,3,1],[0,3,0]])
    requests = [c['input'] for c in cases] * 3
    run = subprocess.run([sys.executable,str(ROOT/'src/Python/main.py')],
        input=''.join(json.dumps(x)+'\n' for x in requests),text=True,
        capture_output=True,check=True,timeout=20)
    answers = [json.loads(line) for line in run.stdout.splitlines()]
    assert len(answers)==len(requests)
    for c, answer in zip(cases*3, answers):
        assert check(c['input'],answer,c['output']), (c,answer)
    (ROOT/'tests/my_cases.jsonl').write_text(''.join(json.dumps(c['input'])+'\n' for c in cases))
    (ROOT/'tests/expected.json').write_text(json.dumps(cases,indent=2))
    (ROOT/'tests/actual.jsonl').write_text(run.stdout)
    # Alternative valid witnesses and deliberately invalid ones.
    x={'task':'kruskal','n':3,'edges':[[0,1,1],[1,2,1],[0,2,1]]}
    e={'cost':2,'components':1}
    assert check(x,dict(e,edge_ids=[0,1]),e)
    assert check(x,dict(e,edge_ids=[0,2]),e)
    assert not check(x,dict(e,edge_ids=[0,0]),e)
    x={'task':'topo','n':3,'edges':[[0,2],[1,2]]}
    assert check(x,{'acyclic':True,'order':[0,1,2]},{'acyclic':True})
    assert check(x,{'acyclic':True,'order':[1,0,2]},{'acyclic':True})
    assert not check(x,{'acyclic':True,'order':[2,0,1]},{'acyclic':True})
    x=cases[10]['input']  # SCC labels can be renamed.
    answer=a.scc(x)
    alt={'component':[v+10 for v in answer['component']],
         'condensation':[[u+10,v+10] for u,v in answer['condensation']]}
    assert check(x,alt,cases[10]['output'])
    alt['condensation']=[]
    assert not check(x,alt,cases[10]['output'])
    x=cases[-1]['input']; result=a.dag(x)
    assert check(x,dict(result,parent_edge=[-1,1,2,4,-1]),cases[-1]['output'])
    assert not check(x,dict(result,parent_edge=[-1,2,2,4,-1]),cases[-1]['output'])
    routes={}
    for target, expected in [(3,[0,3]),(0,[0]),(4,[]),(1,[0,1])]:
        route=a.reconstruct_route(0,target,x['edges'],result['parent_edge'])
        assert route==expected
        ids=[]; v=target
        while route and v!=0:
            i=result['parent_edge'][v]; ids.append(i)
            assert x['edges'][i][1]==v
            v=x['edges'][i][0]
        ids.reverse()
        if route: assert sum(x['edges'][i][2] for i in ids)==result['distance'][target]
        routes[target]={'vertices':route,'edge_ids':ids}
    (ROOT/'tests/routes.json').write_text(json.dumps(routes,indent=2))
    n=100000; m=250000
    ops=[[i%(n-1),i%(n-1)+1] for i in range(m)]
    states=a.dsu({'n':n,'operations':ops})['states']
    assert len(states)==m and states[-1]==[1,n]
    del ops, states
    weighted=[[i,i+1,-1000000000] for i in range(n-1)]
    weighted += [[0,0,-1000000000]]*(m-len(weighted))
    expected={'cost':-(n-1)*1000000000,'components':1}
    for method in (a.kruskal,a.prim):
        x={'task':method.__name__,'n':n,'edges':weighted}
        assert check(x,method(x),expected)
    x={'task':'dag','n':n,'edges':weighted[:n-1],'source':0}
    # Repeated forward edges reach the full m limit without a cycle.
    x['edges'] += [[0,1,-1000000000]]*(m-len(x['edges']))
    result=a.dag(x)
    assert result['distance'][-1]==expected['cost']
    assert len(a.reconstruct_route(0,n-1,x['edges'],result['parent_edge']))==n
    directed=[[u,v] for u,v,w in x['edges']]
    result=a.topo({'n':n,'edges':directed})
    assert result['acyclic'] and result['order']==list(range(n))
    result=a.scc({'n':n,'edges':directed})
    assert len(set(result['component']))==n and len(result['condensation'])==n-1
    print('PASS: 15 own cases x 3 mixed batches; alternative/invalid witnesses; 4 route calls; all six methods at n=100000, q/m=250000.')

if __name__=='__main__': main()

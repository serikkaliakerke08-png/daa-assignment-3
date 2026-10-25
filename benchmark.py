import json
import platform
import random
import statistics
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src/Python'),str(ROOT/'tools')]
import algorithms as a
from public_validate import check


def main():
    report={'python':sys.version,'platform':platform.platform(),
            'processor':platform.processor(),'timer':'time.perf_counter',
            'boundary':'Algorithm call, including internal adjacency/DSU/sorting; excludes generation, parsing, validation and I/O.',
            'warmup':'One untimed call per method per graph','rows':[]}
    for n in (1000,10000,50000):
        seed=2537+n; rng=random.Random(seed)
        edges=[[i,i+1,rng.randint(-1000,1000)] for i in range(n-1)]
        edges += [[rng.randrange(n),rng.randrange(n),rng.randint(-1000,1000)]
                  for _ in range(5*n-len(edges))]
        request={'n':n,'edges':edges}
        k=a.kruskal(request); p=a.prim(request)
        assert k['cost']==p['cost'] and k['components']==p['components']==1
        for task,answer in [('kruskal',k),('prim',p)]:
            assert check(dict(request,task=task),answer,k)
        times={'kruskal':[],'prim':[]}
        for repeat in range(3):
            names=('kruskal','prim') if repeat%2==0 else ('prim','kruskal')
            for name in names:
                start=time.perf_counter(); result=getattr(a,name)(request)
                elapsed=time.perf_counter()-start
                times[name].append(elapsed)
                assert result['cost']==k['cost']
        report['rows'].append({'n':n,'m':len(edges),'seed':seed,'cost':k['cost'],
            'seconds':times,'median_seconds':{name:statistics.median(ts) for name,ts in times.items()}})
    try:
        report['cpu_model']=next(line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name'))
    except (OSError,StopIteration): report['cpu_model']='unavailable'
    (ROOT/'tests/benchmark_results.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()

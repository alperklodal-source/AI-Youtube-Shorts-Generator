"""Search Pixabay/Coverr/Mixkit videos via OpenMontage sources. Usage: search.py "query" [...]"""
import sys, json, inspect, importlib, os
sys.path.insert(0, '/home/user/tools/OpenMontage')
from tools.video.stock_sources.base import SearchFilters
ps = inspect.signature(SearchFilters).parameters
F = SearchFilters(**{k: v.default for k, v in ps.items() if v.default is not inspect._empty})
SRC = ['pixabay_video', 'coverr', 'mixkit']
def sources():
    for mod in SRC:
        m = importlib.import_module(f'tools.video.stock_sources.{mod}')
        cls = [c for n, c in inspect.getmembers(m, inspect.isclass) if n.endswith('Source') and c.__module__ == m.__name__][0]
        yield mod, cls()
if __name__ == '__main__':
    out = {}
    for q in sys.argv[1:]:
        res = []
        for mod, s in sources():
            try:
                for c in s.search(q, F):
                    res.append(dict(src=mod, id=getattr(c, 'source_id', ''), w=c.width, h=c.height, dur=getattr(c, 'duration', 0), tags=(getattr(c, 'source_tags', '') or '')[:80]))
            except Exception as e:
                res.append(dict(src=mod, err=str(e)[:80]))
        out[q] = res
        n = {m: sum(1 for r in res if r.get('src') == m and 'err' not in r) for m in SRC}
        print(f"{q:28s} {n}")
    json.dump(out, open('/home/user/shorts/search_last.json', 'w'), indent=1)

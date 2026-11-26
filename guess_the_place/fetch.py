"""fetch.py OUTDIR "query" id1 id2 ... — download chosen Pixabay/Coverr/Mixkit results by id."""
import sys, json
from pathlib import Path
sys.path.insert(0, '/home/user/shorts/scripts')
from search import sources, F
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
q, ids = sys.argv[2], set(sys.argv[3:])
credits = []
for mod, s in sources():
    try: res = s.search(q, F)
    except Exception: continue
    for c in res:
        if str(getattr(c, 'source_id', '')) in ids:
            p = s.download(c, out / f"{mod}_{c.source_id}.mp4")
            credits.append(dict(file=p.name, src=mod, id=c.source_id, license=c.license,
                                creator=getattr(c, 'creator', '') or getattr(c, 'author', ''), url=getattr(c, 'source_url', '') or getattr(c, 'page_url', '')))
            print('ok', p.name, p.stat().st_size // 1024, 'KB')
cf = out / 'credits.json'
old = json.load(open(cf)) if cf.exists() else []
json.dump(old + credits, open(cf, 'w'), indent=1)

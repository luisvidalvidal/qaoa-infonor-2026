"""Compara el nuevo entrenamiento con la referencia, sin modificar ninguno."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
original=json.loads((ROOT/'reference/experiment_results.json').read_text())
fresh=json.loads((ROOT/'outputs/full.json').read_text())
maxima=dict(energy=0.,probability=0.,parameter=0.,summary=0.)
count=0; changed_status=0
for n in ('4','6','8'):
    for p in ('1','2','3'):
        a=original['main'][n]['depths'][p]; b=fresh['main'][n]['depths'][p]
        assert len(a)==len(b)
        for sa,sb in zip(a,b):
            assert sa['master_seed']==sb['master_seed']
            assert len(sa['runs'])==len(sb['runs'])
            for ra,rb in zip(sa['runs'],sb['runs']):
                count+=1
                maxima['energy']=max(maxima['energy'],abs(ra['energy']-rb['energy']))
                for name,key in [('probability','probs'),('parameter','final')]:
                    maxima[name]=max(maxima[name],max(abs(x-y) for x,y in zip(ra[key],rb[key])))
                changed_status+=int(any(ra[k]!=rb[k] for k in ('success','status','nfev')))
for a,b in zip(original['summary'],fresh['summary']):
    for key in ('feasibility','opt_factor','quality','p_opt_total'):
        maxima['summary']=max(maxima['summary'],max(abs(x-y) for x,y in zip(a[key],b[key])))
report=dict(optimizations_retrained=count,max_absolute_differences=maxima,
            runs_with_changed_termination=changed_status,environment=fresh['metadata'],
            identical_numeric_results=all(v==0 for v in maxima.values()) and changed_status==0)
(ROOT/'outputs/full_comparison.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print(json.dumps(report,indent=2,ensure_ascii=False))

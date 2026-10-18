"""Reproducible statevector QAOA experiment for the INFONOR paper."""
import json, math, platform
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import minimize
from .economics import SECTORS, score, W

ROOT=Path(__file__).resolve().parents[2] / "outputs"
ALPHA=0.35; PENALTY=3.0
MASTER_SEEDS=list(range(20260830,20260835))
MAXITER=420

# Fixed scaling over all 18 sectors.
S=(score-score.min())/(score.max()-score.min())
ORDER=np.argsort(-score)

def instance(n, alpha=ALPHA, penalty=PENALTY):
    if n not in (4, 6, 8):
        raise ValueError('n debe ser 4, 6 u 8')
    idx=ORDER[:n]; k=n//2
    states=((np.arange(2**n)[:,None] >> np.arange(n)) & 1).astype(float)
    s=S[idx]; w=W[np.ix_(idx,idx)]
    linear=states@s
    quadratic=np.einsum('bi,ij,bj->b',states,np.triu(w,1),states)
    F=linear+alpha*quadratic
    counts=states.sum(1)
    C=-F+penalty*(counts-k)**2
    feasible=counts==k
    fmax=F[feasible].max(); opt=(F>=fmax-1e-12)&feasible
    order=np.argsort(F[feasible])[::-1]
    feasible_ids=np.where(feasible)[0]
    second=F[feasible_ids[order[1]]]
    best_id=np.where(opt)[0][0]
    xbest=states[best_id]
    return dict(alpha=alpha,penalty=penalty,n=n,k=k,idx=idx,states=states,s=s,w=w,F=F,C=C,feasible=feasible,
                opt=opt,fmax=fmax,second=second,best_id=best_id,xbest=xbest,
                linear_best=float(linear[best_id]),quadratic_best=float(alpha*quadratic[best_id]))

def statevector_probs(inst, theta, p):
    n=inst['n']; N=2**n
    gamma=np.asarray(theta[:p]); beta=np.asarray(theta[p:])
    amp=np.full(N,1/math.sqrt(N),dtype=complex)
    for layer in range(p):
        amp *= np.exp(-1j*gamma[layer]*inst['C'])
        c=np.cos(beta[layer]); s=-1j*np.sin(beta[layer])
        for q in range(n):
            step=1<<q
            for start in range(0,N,step*2):
                a=np.arange(start,start+step); b=a+step
                va=amp[a].copy(); vb=amp[b].copy()
                amp[a]=c*va+s*vb; amp[b]=s*va+c*vb
    return np.abs(amp)**2

def metrics(inst, probs):
    pf=float(probs[inst['feasible']].sum())
    po=float(probs[inst['opt']].sum())
    cond=po/pf if pf else 0.0
    factor=cond*math.comb(inst['n'],inst['k'])
    qual=float(np.sum(probs[inst['feasible']]*(inst['F'][inst['feasible']]/inst['fmax']))/pf) if pf else 0.0
    return dict(feasibility=pf,p_opt_total=po,p_opt_cond=cond,opt_factor=factor,quality_cond=qual)

def transfer(theta_old,p_old,p_new):
    old_grid=np.linspace(0,1,p_old); new_grid=np.linspace(0,1,p_new)
    g=np.interp(new_grid,old_grid,theta_old[:p_old])
    b=np.interp(new_grid,old_grid,theta_old[p_old:])
    return np.r_[g,b]

def optimize(inst,p,x0):
    def fun(t): return float(statevector_probs(inst,t,p)@inst['C'])
    bounds=[(0,2*np.pi)]*p+[(0,np.pi)]*p
    res=minimize(fun,x0,method='COBYLA',bounds=bounds,
                 options={'maxiter':MAXITER,'rhobeg':0.5,'tol':1e-8,'catol':1e-8})
    probs=statevector_probs(inst,res.x,p)
    return dict(initial=np.asarray(x0).tolist(),final=np.asarray(res.x).tolist(),energy=float(res.fun),
                nfev=int(res.nfev),success=bool(res.success),status=int(res.status),message=str(res.message),
                metrics=metrics(inst,probs),probs=probs.tolist())

def random_start(rng,p): return np.r_[rng.uniform(0,2*np.pi,p),rng.uniform(0,np.pi,p)]

def run_main():
    out={}
    for n in (4,6,8):
        inst=instance(n); runs_by_p={}; previous_best={}
        for p in (1,2,3):
            print(f"Entrenando n={n}, p={p} (5 semillas)", flush=True)
            per_seed=[]
            for master in MASTER_SEEDS:
                rng=np.random.default_rng(np.random.SeedSequence([master,n,p]))
                starts=[random_start(rng,p) for _ in range(12 if p==1 else 16)]
                labels=['random']*len(starts)
                if p>1:
                    starts.append(transfer(previous_best[master]['final'],p-1,p)); labels.append('transfer')
                runs=[]
                for label,x0 in zip(labels,starts):
                    rr=optimize(inst,p,x0); rr['initialization']=label; runs.append(rr)
                best=min(runs,key=lambda r:r['energy']); previous_best[master]=best
                per_seed.append(dict(master_seed=master,best=best,runs=runs))
            runs_by_p[str(p)]=per_seed
        out[str(n)]={'instance':audit_instance(inst),'depths':runs_by_p}
    return out

def audit_instance(inst):
    selected=[SECTORS[inst['idx'][i]] for i,v in enumerate(inst['xbest']) if v]
    uniform=float(np.mean(inst['F'][inst['feasible']]/inst['fmax']))
    return dict(n=inst['n'],k=inst['k'],candidate_indices=(inst['idx']+1).tolist(),
                candidates=[SECTORS[i] for i in inst['idx']],s=inst['s'].tolist(),w=inst['w'].tolist(),
                selected=selected,f_star=float(inst['fmax']),linear=float(inst['linear_best']),
                quadratic=float(inst['quadratic_best']),second=float(inst['second']),
                gap=float(inst['fmax']-inst['second']),uniform_quality=uniform,
                unique_optimum=int(inst['opt'].sum())==1)

def alpha_audit():
    rows=[]
    for a in (0,.1,.35,.5,1.0):
        for n in (4,6,8):
            inst=instance(n,alpha=a)
            rows.append(dict(alpha=a,**audit_instance(inst)))
        # Full 18-sector control with k=4.
        idx=np.arange(18); n=18; k=4
        states=None
        best=(-1,None,None,None); second=-1
        import itertools
        vals=[]
        for comb in itertools.combinations(range(n),k):
            x=np.zeros(n);x[list(comb)]=1
            lin=float(S@x); quad=float(a*np.einsum('i,ij,j',x,np.triu(W,1),x)); f=lin+quad
            vals.append((f,comb,lin,quad))
        vals.sort(reverse=True,key=lambda z:z[0]); f,comb,lin,quad=vals[0]
        rows.append(dict(alpha=a,n=18,k=4,selected=[SECTORS[i] for i in comb],f_star=f,
                         linear=lin,quadratic=quad,second=vals[1][0],gap=f-vals[1][0]))
    return rows

def apply_readout(probs,n,eps=.03):
    ids=np.arange(2**n); xor=ids[:,None]^ids[None,:]
    h=np.vectorize(int.bit_count)(xor.astype(object)).astype(int)
    channel=(eps**h)*((1-eps)**(n-h))
    return channel@np.asarray(probs)

def summaries(main):
    rows=[]; noise=[]
    for n in (4,6,8):
        inst=instance(n)
        for p in (1,2,3):
            seeds=main[str(n)]['depths'][str(p)]
            ms=[s['best']['metrics'] for s in seeds]
            allruns=[r for s in seeds for r in s['runs']]
            def medq(key):
                a=np.array([m[key] for m in ms]); return [float(np.median(a)),float(np.quantile(a,.25)),float(np.quantile(a,.75))]
            rows.append(dict(n=n,p=p,seed_replicates=len(seeds),runs=len(allruns),
                             feasibility=medq('feasibility'),opt_factor=medq('opt_factor'),
                             quality=medq('quality_cond'),p_opt_total=medq('p_opt_total'),
                             exhausted=float(np.mean([r['nfev']>=MAXITER for r in allruns])),
                             optimizer_success=float(np.mean([r['success'] for r in allruns])),
                             random_runs=sum(r['initialization']=='random' for r in allruns),
                             transfer_runs=sum(r['initialization']=='transfer' for r in allruns)))
            if p==3:
                nm=[]
                for s in seeds:
                    q=apply_readout(s['best']['probs'],n,.03); nm.append(metrics(inst,q))
                def nmed(key):return float(np.median([m[key] for m in nm]))
                noise.append(dict(n=n,eps=0.03,p_opt_total=nmed('p_opt_total'),feasibility=nmed('feasibility')))
    return rows,noise

if __name__=='__main__':
    ROOT.mkdir(parents=True, exist_ok=True)
    main=run_main(); rows,noise=summaries(main)
    result=dict(metadata=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                              alpha=ALPHA,penalty=PENALTY,maxiter=MAXITER,seeds=MASTER_SEEDS,
                              scaling='s_i=(r_i-min_all18 r)/(max_all18 r-min_all18 r)'),
                sectors=SECTORS,score_raw=score.tolist(),score_scaled=S.tolist(),alpha_audit=alpha_audit(),
                main=main,summary=rows,noise=noise)
    (ROOT/'experiment_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'summary':rows,'noise':noise},ensure_ascii=False,indent=2))


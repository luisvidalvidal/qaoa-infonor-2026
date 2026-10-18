"""Auditoría independiente de los registros: no vuelve a entrenar COBYLA."""
import csv
import json
from pathlib import Path
import numpy as np
from . import economics as ec
from . import experiment as ex
from .classical import greedy_audit, penalty_audit
from .circuit import ising_coefficients, direct_statevector, decomposed_statevector
ROOT = Path(__file__).resolve().parents[2]

def close(a, b, atol=1e-10):
    np.testing.assert_allclose(a, b, rtol=0, atol=atol)

def compare_tree(a, b):
    if isinstance(a, dict):
        assert a.keys() == b.keys(), (a.keys(), b.keys())
        for k in a: compare_tree(a[k], b[k])
    elif isinstance(a, list):
        assert len(a) == len(b)
        for x, y in zip(a, b): compare_tree(x, y)
    elif isinstance(a, (int, float)) and not isinstance(a, bool): close(a, b)
    else: assert a == b, (a, b)

def verify():
    ref = json.loads((ROOT/'reference/experiment_results.json').read_text())
    assert ref['metadata']['seeds'] == ex.MASTER_SEEDS
    assert ref['metadata']['maxiter'] == ex.MAXITER
    close([ref['metadata']['alpha'], ref['metadata']['penalty']], [ex.ALPHA, ex.PENALTY])
    close(ec.score, ref['score_raw']); close(ex.S, ref['score_scaled'])
    assert ref['sectors'] == ec.SECTORS
    rho = float(max(abs(np.linalg.eigvals(ec.A))))
    assert rho < 1
    with (ROOT/'data/economic_coefficients.csv').open(encoding='utf-8-sig') as f:
        coeff = list(csv.DictReader(f))
    for i, row in enumerate(coeff):
        assert row['sector'] == ec.SECTORS[i]
        close([float(row[k]) for k in ('u_atras','v_adelante','r','s')],
              [ec.back_n[i],ec.forward_n[i],ec.score[i],ex.S[i]])
        assert int(row['orden_r']) == list(ex.ORDER).index(i)+1
    with (ROOT/'data/candidate_W.csv').open(encoding='utf-8-sig') as f: wrows=list(csv.reader(f))
    close(np.array([row[1:] for row in wrows[1:]],float),ec.W[np.ix_(ex.ORDER[:8],ex.ORDER[:8])])
    classical=[]; count=0; max_prob=0.; max_energy=0.; max_gate=0.
    for n in (4,6,8):
        inst=ex.instance(n)
        compare_tree(ex.audit_instance(inst),ref['main'][str(n)]['instance'])
        c,h,J=ising_coefficients(inst); z=1-2*inst['states']
        close(c+z@h+np.einsum('bi,ij,bj->b',z,J,z),inst['C'])
        classical.append(dict(n=n,k=inst['k'],greedy=greedy_audit(inst),penalty=penalty_audit(inst)))
        assert greedy_audit(inst)['matches_exact']
        assert penalty_audit(inst)['cost_gap_best_infeasible_minus_optimum'] > 0
        previous={}
        for p in (1,2,3):
            theta=np.r_[np.linspace(.173,.731,p),np.linspace(.419,1.237,p)]
            err=float(np.max(abs(direct_statevector(inst,theta,p)-decomposed_statevector(inst,theta,p))))
            max_gate=max(max_gate,err); assert err<1e-12
            seeds=ref['main'][str(n)]['depths'][str(p)]
            assert [s['master_seed'] for s in seeds]==ex.MASTER_SEEDS
            for seed in seeds:
                master=seed['master_seed']
                rng=np.random.default_rng(np.random.SeedSequence([master,n,p]))
                expected=[ex.random_start(rng,p) for _ in range(12 if p==1 else 16)]
                if p>1: expected.append(ex.transfer(previous[master]['final'],p-1,p))
                assert len(seed['runs'])==len(expected)
                for index,(run,start) in enumerate(zip(seed['runs'],expected)):
                    close(run['initial'],start)
                    assert run['initialization']==('transfer' if p>1 and index==16 else 'random')
                    probs=ex.statevector_probs(inst,run['final'],p)
                    close(probs.sum(),1); assert (probs>=0).all()
                    pe=float(np.max(abs(probs-run['probs']))); max_prob=max(max_prob,pe)
                    ee=abs(float(probs@inst['C'])-run['energy']); max_energy=max(max_energy,ee)
                    close(probs,run['probs']); close(probs@inst['C'],run['energy'])
                    compare_tree(ex.metrics(inst,probs),run['metrics'])
                    count+=1
                compare_tree(seed['best'], min(seed['runs'],key=lambda r:r['energy']))
                previous[master]=seed['best']
    assert count==690
    compare_tree(classical,json.loads((ROOT/'reference/classical_audit.json').read_text()))
    compare_tree(ex.alpha_audit(),ref['alpha_audit'])
    summary,noise=ex.summaries(ref['main'])
    compare_tree(summary,ref['summary']); compare_tree(noise,ref['noise'])
    # Tabla 4: CSV redondeado de coeficientes, ángulos y distribución.
    with (ROOT/'data/circuit_example_n4.csv').open(encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    lookup={(r['elemento'],r['indice_o_par']):r['valor'] for r in rows}
    inst=ex.instance(4); c,h,J=ising_coefficients(inst)
    for i in range(4):
        assert lookup['qubit_sector',f'q{i}']==ec.SECTORS[inst['idx'][i]]
        close(h[i],float(lookup['h',str(i)]))
        for j in range(i+1,4): close(J[i,j],float(lookup['J',f'{i}{j}']))
    close(c,float(lookup['constante','c']))
    theta=[float(lookup['parametro',k]) for k in ('gamma1','gamma2','beta1','beta2')]
    probs=ex.statevector_probs(inst,theta,2)
    close(probs,[float(lookup['probabilidad',format(i,'04b')]) for i in range(16)])
    close(probs@inst['C'],float(lookup['resultado','energia']))
    for k,v in ex.metrics(inst,probs).items(): close(v,float(lookup['metrica',k]))
    return dict(status='PASS',optimizations_replayed=count,spectral_radius=rho,
                max_probability_error=max_prob,max_energy_error=max_energy,max_gate_error=max_gate,
                training_repeated=False,summary=summary,noise=noise)

if __name__=='__main__':
    result=verify(); (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs/verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps({k:v for k,v in result.items() if k not in ('summary','noise')},indent=2))

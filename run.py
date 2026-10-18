"""Entrada CLI desde la raíz del repositorio, sin instalación editable."""
from pathlib import Path
import argparse, json, sys, platform, time
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['verify','demo','full'])
    args=parser.parse_args()
    from qaoa_infonor import experiment as ex
    import numpy as np, scipy
    out=ROOT/'outputs'; out.mkdir(exist_ok=True)
    start=time.perf_counter()
    if args.mode=='verify':
        from qaoa_infonor.verify import verify
        result=verify()
    elif args.mode=='demo':
        inst=ex.instance(4); rng=np.random.default_rng(20260830)
        runs=[ex.optimize(inst,1,ex.random_start(rng,1)) for _ in range(2)]
        result=dict(mode='demo',note='Dos inicios nuevos: no reproduce las tablas del protocolo completo.',
                    instance=ex.audit_instance(inst),best=min(runs,key=lambda r:r['energy']),runs=runs)
    else:
        print('Protocolo completo: 690 optimizaciones; puede tardar. Los registros originales se conservan.',flush=True)
        main_runs=ex.run_main(); summary,noise=ex.summaries(main_runs)
        result=dict(metadata=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                    alpha=ex.ALPHA,penalty=ex.PENALTY,maxiter=ex.MAXITER,seeds=ex.MASTER_SEEDS,
                    scaling='s_i=(r_i-min_all18 r)/(max_all18 r-min_all18 r)'),
                    sectors=ex.SECTORS,score_raw=ex.score.tolist(),score_scaled=ex.S.tolist(),
                    alpha_audit=ex.alpha_audit(),main=main_runs,summary=summary,noise=noise)
    path=out/f'{args.mode}.json'; path.write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(f'OK: {path.name}; tiempo {time.perf_counter()-start:.2f} s')
    if args.mode=='verify': print(json.dumps({k:v for k,v in result.items() if k not in ('summary','noise')},indent=2))
if __name__=='__main__': main()

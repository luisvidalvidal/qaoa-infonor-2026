from pathlib import Path
import json,base64,zipfile,io,hashlib
r=Path(__file__).resolve().parents[1]
b=io.BytesIO()
with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
 for sub in ['src','data','reference','tests']:
  for p in sorted((r/sub).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts: z.write(p,p.relative_to(r))
 for f in ['run.py','requirements.txt']: z.write(r/f,f)
payload=base64.b64encode(b.getvalue()).decode(); digest=hashlib.sha256(b.getvalue()).hexdigest()
cells=[]
def md(s): cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s): cells.append(dict(cell_type='code',execution_count=None,outputs=[],metadata={},source=s.splitlines(True)))
md('''# QAOA INFONOR 2026 — reproducción verificable
**Luis Hernán Vidal Vidal y María Soledad Pérez Sandoval**

Notebook autónomo: incluye código, cuatro CSV y los dos JSON originales. Ejecute las celdas en orden en un entorno CPU. No requiere GitHub ni otros archivos. La primera instalación necesita Internet si faltan las versiones fijadas.

**Tres niveles distintos:** auditoría de los resultados recibidos, demostración con dos entrenamientos nuevos y entrenamiento completo opcional (690 optimizaciones). Simulación exacta clásica, sin shots ni hardware cuántico; no demuestra ventaja cuántica.

La MIP estimada corresponde a 2016, no a la economía regional actual. Fuente declarada: Miranda Castillo et al. (2019), DOI 10.25115/eea.v37i1.2581. Se audita el material entregado; no se vuelve a validar la digitalización contra esa publicación.
''')
code('''# 1. Recuperar el paquete incluido. No se sobrescriben archivos existentes diferentes.
from pathlib import Path
import base64, hashlib, io, json, os, subprocess, sys, zipfile
ROOT = Path.cwd() / "qaoa_infonor_colab"
ROOT.mkdir(exist_ok=True)
PAYLOAD = "'''+payload+'''"
raw = base64.b64decode(PAYLOAD)
assert hashlib.sha256(raw).hexdigest() == "'''+digest+'''", "Paquete alterado"
with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    for item in archive.infolist():
        dest = (ROOT / item.filename).resolve()
        if ROOT.resolve() not in dest.parents:
            raise ValueError("Ruta no permitida")
        data = archive.read(item)
        if dest.exists() and dest.read_bytes() != data:
            raise RuntimeError(f"Existe una versión modificada: {dest}. Cambie ROOT para una ejecución limpia.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
(ROOT / "outputs").mkdir(exist_ok=True)
print("Paquete recuperado:", ROOT)
''')
code('''# 2. Dependencias científicas. Reutiliza el intérprete solo si coincide exactamente.
probe = "import numpy, scipy; assert numpy.__version__ == '2.3.5' and scipy.__version__ == '1.17.0'"
if sys.version_info < (3,11):
    raise RuntimeError("Seleccione un entorno Python 3.11 o posterior; recomendado 3.12")
check = subprocess.run([sys.executable, "-c", probe], capture_output=True)
if check.returncode == 0:
    PYTHON = sys.executable
else:
    deps = ROOT / ".dependencies"
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "--target", str(deps), "-r", str(ROOT / "requirements.txt")], check=True)
    os.environ["PYTHONPATH"] = str(deps) + os.pathsep + os.environ.get("PYTHONPATH", "")
    PYTHON = sys.executable
subprocess.run([PYTHON, "-c", probe], check=True)
def run_script(source):
    preamble = "import sys; sys.path.insert(0, 'src')\\n"
    result = subprocess.run([PYTHON, "-c", preamble + source], cwd=ROOT, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode:
        raise RuntimeError(result.stderr)
run_script("import platform, numpy, scipy; print('Python', platform.python_version(), 'NumPy', numpy.__version__, 'SciPy', scipy.__version__)")
''')
md('''## 3. Auditoría de las 690 corridas registradas
Se recalculan las distribuciones desde los ángulos finales, las energías y métricas, la secuencia de inicializaciones, los controles clásicos y los resúmenes. **Esto no vuelve a entrenar COBYLA.** Se exige tolerancia absoluta 1e-10 para los registros y 1e-12 para la equivalencia de puertas.
''')
code('''result = subprocess.run([PYTHON, "run.py", "verify"], cwd=ROOT, capture_output=True, text=True)
print(result.stdout)
assert result.returncode == 0, result.stderr
report = json.loads((ROOT / "outputs/verify.json").read_text())
assert report["optimizations_replayed"] == 690
result = subprocess.run([PYTHON, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, capture_output=True, text=True)
print(result.stdout + result.stderr)
assert result.returncode == 0
''')
md('''## 4. Tablas del paper
Las tablas se reconstruyen desde los datos y distribuciones contrastados. Las cifras del Word están redondeadas. Las medianas no se deben multiplicar para reconstruir la mediana de un producto.
''')
code('''from IPython.display import display, Markdown
import csv
reference = json.loads((ROOT / "reference/experiment_results.json").read_text())
def show_table(title, headers, rows):
    def fmt(v):
        return f"{v:.6f}" if isinstance(v, float) else str(v).replace("|", "/")
    lines = ["### " + title, "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in rows]
    display(Markdown("\\n".join(lines)))
with (ROOT / "data/economic_coefficients.csv").open(encoding="utf-8-sig") as f:
    coeff = sorted(csv.DictReader(f), key=lambda r: int(r['orden_r']))[:8]
show_table("Tabla 2: candidatos", ["Sector", "u", "v", "r", "s"],
           [[r['sector']] + [float(r[k]) for k in ['u_atras','v_adelante','r','s']] for r in coeff])
show_table("Tabla 3: recursos lógicos para p=3", ["n", "Amplitudes", "H", "RZZ", "CNOT", "RZ campos", "RX"],
           [[n,2**n,n,3*n*(n-1)//2,3*n*(n-1),3*n,3*n] for n in [4,6,8]])
show_table("Tabla 5: óptimo exacto", ["n", "k", "Sectores", "F*", "Brecha"],
           [[x['instance']['n'],x['instance']['k'], '; '.join(x['instance']['selected']), x['instance']['f_star'],x['instance']['gap']] for x in reference['main'].values()])
def interval(values): return f"{values[0]:.6f} [{values[1]:.6f}; {values[2]:.6f}]"
show_table("Tabla 6: medianas [Q1; Q3]", ["n","p","Factibilidad","Factor G","Calidad Q","Q uniforme","Agotamiento %"],
           [[r['n'],r['p'],interval(r['feasibility']),interval(r['opt_factor']),r['quality'][0], reference['main'][str(r['n'])]['instance']['uniform_quality'],100*r['exhausted']] for r in report['summary']])
show_table("Tabla 7: sensibilidad exacta", ["alpha", "n", "k", "Selección", "F*"],
           [[r['alpha'],r['n'],r['k'],'; '.join(r['selected']),r['f_star']] for r in reference['alpha_audit']])
base={r['n']:r for r in report['summary'] if r['p']==3}
show_table("Tabla 8: error de lectura 3%", ["n", "P óptimo sin error", "P óptimo con error", "Factibilidad sin error", "Factibilidad con error"],
           [[r['n'],base[r['n']]['p_opt_total'][0],r['p_opt_total'],base[r['n']]['feasibility'][0],r['feasibility']] for r in report['noise']])
''')
md('''## 5. Ejemplo del circuito de cuatro qubits (Tabla 4)
Qubit q0 = Alimentos; q1 = Silvoagropecuario; q2 = Pesca; q3 = Textil. La cadena se escribe q3 q2 q1 q0: `0011` selecciona Alimentos y Silvoagropecuario. La constante de Ising solo aporta fase global, pero se conserva en la energía. Las rotaciones son RZ(2γh), RZZ(2γJ) y RX(2β).
''')
code('''run_script("""
import csv, numpy as np
from qaoa_infonor.experiment import instance, statevector_probs, metrics
from qaoa_infonor.circuit import ising_coefficients
with open('data/circuit_example_n4.csv',encoding='utf-8-sig') as f:
    rows=list(csv.DictReader(f))
lookup={(r['elemento'],r['indice_o_par']):r['valor'] for r in rows}
theta=[float(lookup['parametro',k]) for k in ('gamma1','gamma2','beta1','beta2')]
inst=instance(4); c,h,J=ising_coefficients(inst)
probs=statevector_probs(inst,theta,2)
print('c =',c); print('h =',h); print('J (triangular superior) ='); print(J)
print('Ángulos =',theta); print('Energía =',probs@inst['C'])
print('Métricas:',metrics(inst,probs))
for i,prob in enumerate(probs): print(format(i,'04b'),f'{prob:.9f}')
""")
''')
md('''## 6. Dos optimizaciones nuevas de demostración
Prueba breve de funcionamiento con n=4, p=1. No debe confundirse con las 690 corridas del protocolo del paper.
''')
code('''result = subprocess.run([PYTHON,"run.py","demo"],cwd=ROOT,capture_output=True,text=True)
print(result.stdout)
assert result.returncode == 0, result.stderr
demo=json.loads((ROOT/'outputs/demo.json').read_text())
print('Energía de la mejor corrida:',demo['best']['energy'])
print('Métricas:',demo['best']['metrics'])
''')
md('''## 7. Opcional: volver a entrenar el protocolo completo
Cambie `RUN_FULL` a `True`. Ejecuta 690 optimizaciones, con hasta 289.800 evaluaciones de costo; el tiempo depende del equipo. Mantiene intactos los registros originales. Las versiones de dependencias están fijadas; aun así, cambios de plataforma pueden modificar la trayectoria numérica. Si se interrumpe esta etapa, debe reiniciarse.
''')
code('''RUN_FULL = False
if RUN_FULL:
    subprocess.run([PYTHON,"run.py","full"],cwd=ROOT,check=True)
    fresh=json.loads((ROOT/'outputs/full.json').read_text())
    rows=[]
    for original,new in zip(reference['summary'],fresh['summary']):
        rows.append([new['n'],new['p'],new['feasibility'][0]-original['feasibility'][0],
                     new['opt_factor'][0]-original['opt_factor'][0],new['quality'][0]-original['quality'][0]])
    show_table('Diferencias de nuevas medianas respecto del registro',["n","p","Δ factibilidad","Δ G","Δ Q"],rows)
else:
    print('Entrenamiento completo omitido. Cambie RUN_FULL=True para ejecutarlo.')
''')
md('''## 8. Exportar resultados
Se exportan los informes calculados en esta sesión. Los registros originales están dentro del notebook y del repositorio. Active la descarga si está trabajando en Colab.
''')
code('''import shutil
archive_path=shutil.make_archive(str(ROOT/'resultados_qaoa'),'zip',ROOT/'outputs')
print('Resultados:',archive_path)
DOWNLOAD_RESULTS = False
if DOWNLOAD_RESULTS:
    from google.colab import files
    files.download(archive_path)
''')
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python',version='3.12'),colab=dict(name='QAOA_INFONOR_Colab.ipynb',provenance=[])),cells=cells)
for i,c in enumerate(cells): c['id']=f'qaoa-{i:02}'
(r/'notebooks/QAOA_INFONOR_Colab.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1))

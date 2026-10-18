# QAOA INFONOR 2026 — material reproducible

Material del artículo: 

**Computación cuántica híbrida para la priorización sectorial: prueba de concepto con QAOA**

**Hybrid quantum computing for sector prioritization: a QAOA proof of concept**

Luis Hernán Vidal Vidal¹. ORCID iD: 0000-0001-8082-084X

María Soledad Pérez Sandoval¹. ORCID iD: 0009-0009-3054-4694

¹Quantum NYX SpA. Valdivia, Chile. E-mail: lvidal@lek.cl; soledad.perez@lek.cl

Simulación clásica exacta del circuito QAOA; **no demuestra ventaja cuántica**. No requiere Qiskit, GPU, cuenta de proveedor cuántico ni claves API.

## Inicio en Google Colab

1. Abra https://colab.research.google.com/ y seleccione **Archivo → Subir notebook**.
2. Suba `notebooks/QAOA_INFONOR_Colab.ipynb`.
3. Seleccione un entorno **CPU** y ejecute las celdas en orden.
4. El notebook contiene una copia comprimida del código, los CSV y los registros originales. No necesita subir otros archivos ni editar una URL de GitHub.
5. Se verifican las 690 distribuciones registradas, se reconstruyen tablas, se muestra el ejemplo de cuatro qubits y se ejecutan dos optimizaciones nuevas.
6. Para entrenar las 690 optimizaciones desde cero, cambie `RUN_FULL = False` a `True` en la celda opcional. La duración depende del procesador. Si se interrumpe, esta versión reinicia el entrenamiento completo.

Si las versiones del intérprete ya coinciden, el notebook las reutiliza. En caso contrario, instala NumPy 2.3.5 y SciPy 1.17.0 en una carpeta de dependencias usada por procesos Python separados para evitar conflictos con librerías precargadas de Colab. Requiere Internet para instalar dependencias. La verificación no necesita Internet después de esa instalación.

## Ejecución local

Entorno original declarado: Python 3.12.13, NumPy 2.3.5, SciPy 1.17.0. Se recomienda Python 3.12; el proyecto requiere al menos 3.11.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py verify
python -m unittest discover -s tests -v
python run.py demo
# Opcional; entrenamiento completo:
python run.py full
python scripts/compare_full.py
```

| Modo | Qué hace | Qué permite afirmar |
|---|---|---|
| `verify` | Reconstruye economía, controles clásicos, Ising, 690 distribuciones desde ángulos finales, inicializaciones, métricas, sensibilidad y resúmenes | Consistencia numérica de los registros entregados; no reentrena |
| `demo` | Dos optimizaciones nuevas, n=4 y p=1 | El optimizador y simulador funcionan; no sustituye las tablas |
| `full` | Ejecuta las 690 optimizaciones con el protocolo original | Nuevo entrenamiento; comparar con `reference/` |

Resultados nuevos en `outputs/`. Los registros suministrados permanecen en `reference/`. No se sobrescriben para forzar coincidencias. Incluso con versiones fijas, diferencias de plataforma y álgebra lineal pueden alterar trayectorias de COBYLA; las verificaciones a parámetros fijos son una comprobación distinta y más estable.

## Estructura

- `notebooks/`: notebook autónomo para Colab.
- `src/qaoa_infonor/economics.py`: lectura del CSV, A, L, encadenamientos y W.
- `src/qaoa_infonor/experiment.py`: formulación, QAOA, COBYLA, sensibilidad y ruido.
- `src/qaoa_infonor/circuit.py`: transformación Ising y puertas RZ, CNOT y RX.
- `src/qaoa_infonor/classical.py`: heurística voraz y umbral de penalización.
- `src/qaoa_infonor/verify.py`: auditoría de los archivos de referencia.
- `data/`: los cuatro CSV recibidos, sin modificar sus valores.
- `reference/`: los dos JSON recibidos, sin modificar sus valores.
- `tests/`: pruebas automatizadas.
- `docs/`: metodología, trazabilidad y validación realizada.
- `.github/workflows/tests.yml`: comprobación automática en GitHub.
- `manifest_sha256.txt`: integridad de los archivos distribuidos.

No se incluye una licencia de redistribución: los autores deben definirla y comprobar los permisos de los datos antes de atribuir una licencia al conjunto. La ausencia de licencia no equivale a dominio público. El Word no se duplica en el repositorio; es el documento de referencia del encargo.

## Datos y alcance

La MIP estimada corresponde a 2016, no a la economía regional actual. Fuente declarada: J. C. Miranda Castillo, C. Ramos Carvajal, R. Reyes Irigoyen, F. Acum Boassi y L. H. Vidal Vidal, “La evolución económica de la Región de Los Ríos desde su creación, a partir de un análisis input-output”, Estud. Econ. Apl., vol. 37, no. 1, pp. 170–191, 2019, doi: 10.25115/eea.v37i1.2581. Se audita el material entregado; no se vuelve a validar la digitalización contra esa publicación.

`docs/METODOLOGIA.md` explica los límites de las conclusiones y el vínculo entre el código y las tablas del paper.

## Mantener el notebook

Después de cambiar código, datos o referencias, ejecute `python scripts/build_notebook.py` para renovar el paquete integrado. No edite manualmente la cadena comprimida. El notebook es una instantánea del código, no descarga cambios automáticamente.

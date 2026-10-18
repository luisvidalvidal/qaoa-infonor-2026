# Metodología y trazabilidad

## Datos → decisión → circuito

El CSV `input_output_2016.csv` contiene 18 filas sectoriales, 18 columnas de transacciones Z y una columna VBP. Las filas representan oferentes; las columnas, usuarios. La unidad declarada en el paper es millones de pesos. Se mantienen los valores entregados, incluidos redondeos de la digitalización.

Se calcula A_ij=Z_ij/X_j, L=(I-A)^(-1), u=sumas de columnas normalizadas por su media y v=sumas de filas normalizadas por su media. r=(u+v)/2; s=(r-min(r))/(max(r)-min(r)). W=(L+L.T)/2, diagonal cero y normalización por el máximo fuera de diagonal. Todas las normalizaciones usan los 18 sectores, antes del recorte a candidatos.

Los candidatos son los primeros n=4,6,8 por r decreciente, con k=n/2. Se maximiza:

`F(x) = s·x + alpha * sum(i<j, W_ij x_i x_j)`

Se minimiza:

`C(x) = -F(x) + P*(sum(x)-k)^2`, con alpha=0.35 y P=3.

QUBO: q_i=P(1-2k)-s_i; q_ij=2P-alpha W_ij. Ising: x_i=(1-z_i)/2, J_ij=q_ij/4, h_i=-q_i/2-sum(j!=i,q_ij)/4; c=Pk²+sum(q_i)/2+sum(i<j,q_ij)/4. La constante se conserva al calcular energía.

QAOA comienza en amplitudes uniformes. Por capa aplica exp(-i gamma C), luego exp(-i beta sum X). La descomposición lógica es RZ(2 gamma h), RZZ(2 gamma J) y RX(2 beta); RZZ=CNOT–RZ–CNOT. `apply_rx` recibe beta, no el ángulo completo 2 beta. Se comprueba igualdad de amplitudes incluyendo la fase global.

**Orden binario:** el qubit q0 es el bit menos significativo. La cadena `0011` se escribe q3 q2 q1 q0 y selecciona los candidatos q0 y q1. El vector de decisiones interno se almacena x0,x1,... .

## Protocolo original conservado

Cinco semillas maestras 20260830–20260834. Para cada n,p, el generador es `default_rng(SeedSequence([master,n,p]))`. Se generan 12 inicios para p=1; 16 aleatorios más uno interpolado del mejor resultado de la misma semilla para p=2 y p=3. Ángulos en orden `[gamma_1,...,gamma_p,beta_1,...,beta_p]`, uniformes en [0,2pi] y [0,pi]. Se usa COBYLA, maxiter=420, rhobeg=0.5, tol=catol=1e-8. Se selecciona la energía mínima, no la máxima probabilidad del óptimo.

Total: 3 tamaños × 5 semillas × (12+17+17) = 690 optimizaciones. El parámetro maxiter de esta llamada limita evaluaciones de función. La demo usa solo dos inicios y se identifica separadamente.

Las medianas y cuartiles se calculan sobre cinco mejores corridas por configuración; los porcentajes de agotamiento y éxito sobre 60 u 85 corridas. El ruido es un canal de inversión de cada bit con probabilidad 0.03, aplicado a distribuciones exactas. No hay shots ni ruido de puertas ni hardware.

## Correspondencia con el artículo

| Elemento | Reconstrucción |
|---|---|
| Tabla 1, ecuaciones económicas | `economics.py` |
| Tabla 2 | CSV de coeficientes, recalculado y contrastado por `verify()` |
| Tabla 3 | Conteos: n H; p*n*(n-1)/2 RZZ; doble CNOT; p*n RZ de campo y RX |
| Tabla 4 | `circuit_example_n4.csv`, contraste de coeficientes, ángulos, energía y 16 probabilidades |
| Tabla 5 | `audit_instance`, enumeración exacta y heurística voraz |
| Tabla 6 | `summaries`: medianas, cuartiles y estados del optimizador |
| Tabla 7 | `alpha_audit`: alpha=0,0.1,0.35,0.5,1; incluye 3060 combinaciones de 18 sectores, k=4 |
| Tabla 8 | `apply_readout` y `summaries` |
| Tabla 9 | Propuesta futura; no es resultado computacional |

El notebook muestra las tablas numéricas derivadas. No intenta replicar el diseño editorial de las figuras originales. Los valores impresos del Word tienen redondeos; los JSON conservan la precisión numérica entregada.

## Qué cambia respecto del código adjunto

Se eliminan sufijos `(1)` y dependencias de nombres incompatibles. Se centralizan los datos en el CSV, se organizan imports como paquete y se separan salidas y referencias. Se añade CLI, notebook autónomo, auditoría de 690 registros, pruebas y flujo GitHub. Los cálculos del protocolo se conservan. Los auxiliares de Ising y auditoría clásica usan los valores alpha/P de cada instancia, evitando constantes equivocadas si se cambia la configuración.

## Límites científicos

La verificación reconstruye el estado final de cada corrida y comprueba la selección del mejor registro y las inicializaciones. No demuestra que cada trayectoria histórica de COBYLA haya ocurrido ni equivale a repetir el entrenamiento. El modo `full` permite esa repetición. Las instancias son pequeñas y preseleccionadas; la heurística voraz alcanza sus óptimos. No se demuestra aceleración, ventaja cuántica, causalidad económica ni validez como diagnóstico regional actual. Los presupuestos difieren con p; el efecto de profundidad no está aislado.

Una vez publicado el repositorio, conviene actualizar la sección 6 del paper con su URL, etiqueta/commit y condiciones de reproducción, sustituyendo la frase que señala que no existe depósito público. No se ha editado el paper. Revise también la declaración de uso de IA para reflejar esta asistencia en reorganización, código de verificación y notebook.

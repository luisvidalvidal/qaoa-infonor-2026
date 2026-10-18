# Validación de esta entrega

Fecha: 18 de octubre de 2026.

## Pruebas realizadas

- Reconstrucción de los coeficientes económicos desde el CSV y comparación con los archivos entregados.
- Enumeración exacta, heurística voraz y umbrales de penalización de n=4,6,8.
- Comprobación del costo QUBO frente a Ising en todos los estados de las tres instancias.
- Reejecución del circuito a los ángulos finales de las 690 corridas: error máximo absoluto de probabilidades y energías igual a cero en este entorno.
- Comparación de inicializaciones, selección de mejores corridas, resúmenes, sensibilidad a alpha y ruido de lectura.
- Verificación del ejemplo de cuatro qubits con el CSV entregado.
- Equivalencia de puertas frente al operador diagonal: error máximo 4.2163e-15.
- Tres pruebas automatizadas aprobadas, incluidas configuraciones alpha/P diferentes y límites del canal de lectura.
- Dos entrenamientos nuevos de demostración completados.
- Notebook validado contra el esquema nbformat; sus ocho celdas de código ejecutadas secuencialmente en un mismo contexto Python, sin errores.

## Alcance de la prueba del notebook

No se inició una sesión real de Google Colab. El entorno de validación bloquea los sockets requeridos por el kernel Jupyter; por ello, se ejecutó el contenido de las celdas directamente y en orden. Se probaron tanto la ruta que reutiliza las dependencias exactas instaladas como la instalación aislada mediante pip --target en una carpeta nueva; ambas pasaron. Estas pruebas se realizaron localmente. La interfaz y el botón de descarga de Google Colab no se probaron desde el servicio. El código no usa GPU ni servicios cuánticos.

El modo opcional de entrenamiento completo se valida separadamente mediante la misma entrada CLI que invoca el notebook.

## Reentrenamiento completo

Se ejecutaron desde cero las 690 optimizaciones con las mismas semillas, límites y reinicios del protocolo.

Máximas diferencias absolutas frente al JSON recibido:

| Variable | Diferencia |
|---|---|
| energy | 0 |
| probability | 0 |
| parameter | 0 |
| summary | 0 |

Corridas con cambios en éxito, estado o número de evaluaciones: 0.

El detalle y las versiones del entorno se conservan en `full_comparison.json`. La coincidencia en este entorno no garantiza igualdad bit a bit en otras plataformas.

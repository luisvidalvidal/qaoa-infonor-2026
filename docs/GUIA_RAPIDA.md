# Guía rápida para los autores

## Probar ahora
1. Abra Google Colab: https://colab.research.google.com/
2. Archivo → Subir notebook → seleccione QAOA_INFONOR_Colab.ipynb.
3. Ejecute todas las celdas en un entorno CPU. El notebook incluye los datos.
4. Compruebe `PASS` y revise las tablas y la demo.
5. Para repetir las 690 optimizaciones, active `RUN_FULL = True`.

## Subir a GitHub
1. Descomprima qaoa_infonor_github.zip.
2. Cree un repositorio en su cuenta.
3. Suba el contenido de qaoa-infonor, respetando subcarpetas.
4. Verifique el flujo Reproducibility en Actions.
5. Cree una versión etiquetada y consigne su URL/commit en el paper.

## Para la justificación del paper
La verificación a parámetros fijos y el entrenamiento nuevo son pruebas distintas. Consulte VALIDACION.md para conocer cuáles se completaron en esta entrega. Los registros originales están preservados; no se han cambiado los datos del artículo. Este material aporta trazabilidad y comprobación numérica; no demuestra ventaja cuántica ni reemplaza la revisión científica.

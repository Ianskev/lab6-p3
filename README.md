# PostgreSQL GIN Index Benchmark

Este proyecto evalúa el rendimiento de los índices GIN (Generalized Inverted Index) en PostgreSQL para búsquedas de texto completo.

## Descripción

El script `run_gin_benchmark.py` realiza pruebas de rendimiento comparativas entre consultas con y sin índices GIN en tablas de diferentes tamaños, midiendo el tiempo de ejecución y generando visualizaciones y análisis de resultados.

## Requisitos

- PostgreSQL (con la función personalizada `test_search_performance`)
- Python 3.x
- Librerías: psycopg2, matplotlib, pandas, numpy

## Estructura del Proyecto

```
EXPERIMENTOS/
├── run_gin_benchmark.py     # Script principal
├── analyze_plans.py         # Analiza los planes de ejecución
├── average_times/           # CSV con tiempos promedio
├── performance/             # Gráficos y datos de rendimiento
├── plans/                   # Planes de ejecución de PostgreSQL
└── log/                     # Archivos de registro
```

## Parámetros de Prueba

El benchmark ejecuta pruebas con las siguientes variables:

- **Tamaños de tabla:** 100, 1000, 10000, 100000, 1000000, 10000000 filas
- **Términos de búsqueda:** "health"
- **Valores top-k:** 5, 10, 15 resultados
- **Uso de índice:** Con índice GIN vs. Sin índice

## Cómo Funciona

1. **Configuración inicial:**
   - Establece la conexión a PostgreSQL
   - Crea directorios para organizar resultados
   - Configura el sistema de logging

2. **Ejecución de pruebas:**
   - Para cada combinación de tamaño de tabla, término de búsqueda y valor top-k:
     - Ejecuta la consulta con y sin índice GIN
     - Registra el tiempo de ejecución y número de resultados
     - Para tablas muy grandes (>10M filas), solo ejecuta con índice

3. **Recopilación de planes de ejecución:**
   - Guarda los planes de ejecución EXPLAIN ANALYZE para casos seleccionados

4. **Generación de visualizaciones:**
   - Rendimiento por tamaño de tabla
   - Rendimiento por valor de top-k
   - Factor de aceleración por tamaño de tabla
   - Impacto de top-k en la aceleración

5. **Análisis de resultados:**
   - Genera tablas pivote para análisis de tiempos promedio
   - Guarda todos los resultados en archivos CSV

## Ejecución

Para ejecutar el benchmark:

```bash
python run_gin_benchmark.py
python analyze_plans.py
```

## Outputs

- **Visualizaciones:** `performance/gin_index_performance.png`
- **Datos brutos:** `performance/gin_index_performance_results_all.csv`
- **Datos filtrados:** `performance/gin_index_performance_results.csv`
- **Tiempos promedio:** `average_times/average_times_by_size.csv` y `average_times/average_times_by_topk.csv`
- **Planes de ejecución:** `plans/plan_{size}_{term}_{topk}_idx{Yes|No}.txt`
- **Logs:** `log/gin_benchmark_{timestamp}.log`

## Nota Importante

Este script asume que:

1. Existe una función PostgreSQL llamada `test_search_performance` para realizar las pruebas
2. Las tablas de prueba siguen el formato `articles_{size}` y contienen columnas `id`, `title`, `content` y un índice GIN llamado `text_vector`

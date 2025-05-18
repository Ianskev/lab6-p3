#!/usr/bin/env python
# filepath: c:\Users\Ian\Desktop\UTEC\CICLO 5\prueba2\run_gin_benchmark.py

import psycopg2
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import os

# Create necessary directories for file organization
os.makedirs('average_times', exist_ok=True)
os.makedirs('performance', exist_ok=True)
os.makedirs('plans', exist_ok=True)
os.makedirs('log', exist_ok=True)  # Added log directory

# Configurar logging
log_filename = f"log/gin_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

# Configuración de conexión a la base de datos
# Ajusta estos parámetros según tu configuración
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="postgres",
    host="localhost"
)
conn.autocommit = True
cursor = conn.cursor()

# Establecer timeout para consultas largas (30 segundos)
cursor.execute("SET statement_timeout = 1200000;")

logging.info("Starting GIN index benchmark experiment")

# Términos de búsqueda para probar
search_terms = ["health"]

# Tamaños de tablas a probar
table_sizes = [100, 1000, 10000, 100000, 1000000, 10000000]

# Valores de top-k a probar
top_k_values = [5, 10, 15]

# Estructura para almacenar resultados
results = []

# Ejecutar pruebas
for table_size in table_sizes:
    table_name = f"articles_{table_size}"
    logging.info(f"Testing table with {table_size} rows")
    
    for search_term in search_terms:
        for top_k in top_k_values:
            # Para tablas grandes, solo ejecutamos pruebas con índice
            use_indices = [True, False] if table_size <= 10000000 else [True]
            
            for use_index in use_indices:
                try:
                    logging.info(f"Running test: {table_name}, term='{search_term}', " +
                                f"top_k={top_k}, index={'Yes' if use_index else 'No'}")
                    
                    # Ejecutar la prueba de rendimiento
                    cursor.execute(
                        """
                        SELECT * FROM test_search_performance(%s, %s, %s, %s);
                        """,
                        (table_name, search_term, top_k, use_index)
                    )
                    row = cursor.fetchone()
                    
                    # Guardar resultados
                    results.append({
                        'table_size': table_size,
                        'search_term': search_term,
                        'top_k': top_k,
                        'index': 'Yes' if use_index else 'No',
                        'query_time_ms': row[1],
                        'result_count': row[2]
                    })
                    
                    logging.info(f"Query time: {row[1]:.2f}ms, Results: {row[2]}")
                    
                    # Obtener el plan de ejecución para algunos casos seleccionados
                    if top_k == 15 and search_term == "health":
                        plan_query = f"""
                        EXPLAIN ANALYZE
                        SELECT id, title FROM {table_name}
                        WHERE {"text_vector" if use_index else "to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(content, ''))"} 
                            @@ plainto_tsquery('english', '{search_term}')
                        ORDER BY ts_rank({"text_vector" if use_index else "to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(content, ''))"}, 
                                        plainto_tsquery('english', '{search_term}')) DESC
                        LIMIT {top_k};
                        """
                        
                        logging.info(f"Getting execution plan for {table_size} rows...")
                        cursor.execute(plan_query)
                        plan = cursor.fetchall()
                        
                        plan_file = os.path.join('plans', f"plan_{table_size}_{search_term}_{top_k}_idx{'Yes' if use_index else 'No'}.txt")
                        with open(plan_file, 'w') as f:
                            for line in plan:
                                f.write(f"{line[0]}\n")
                                logging.info(line[0])
                        
                        logging.info(f"Plan saved to {plan_file}")
                
                except Exception as e:
                    logging.error(f"Error in test: {str(e)}")
                    results.append({
                        'table_size': table_size,
                        'search_term': search_term,
                        'top_k': top_k,
                        'index': 'Yes' if use_index else 'No',
                        'query_time_ms': None,
                        'result_count': None,
                        'error': str(e)
                    })

# Convertir resultados a DataFrame y filtrar errores
df = pd.DataFrame([r for r in results if 'error' not in r])
df_all = pd.DataFrame(results)

logging.info("Creating visualizations...")

# Gráfico comparativo de tiempos de ejecución
plt.figure(figsize=(16, 12))

# 1. Tiempos por tamaño de tabla
plt.subplot(2, 2, 1)
df_avg = df.groupby(['table_size', 'index'])['query_time_ms'].mean().reset_index()
for idx, use_index in enumerate(['No', 'Yes']):
    data = df_avg[df_avg['index'] == use_index]
    if not data.empty:
        plt.plot(data['table_size'], data['query_time_ms'], marker='o', 
                label=f"Con Índice: {use_index}", linewidth=2)
plt.xscale('log')
plt.yscale('log')
plt.xlabel('Tamaño de Tabla (filas)')
plt.ylabel('Tiempo de Consulta Promedio (ms)')
plt.title('Rendimiento de Consulta por Tamaño de Tabla')
plt.legend()
plt.grid(True)

# 2. Tiempos por valor de top-k
plt.subplot(2, 2, 2)
df_avg = df.groupby(['top_k', 'index'])['query_time_ms'].mean().reset_index()
for idx, use_index in enumerate(['No', 'Yes']):
    data = df_avg[df_avg['index'] == use_index]
    if not data.empty:
        plt.plot(data['top_k'], data['query_time_ms'], marker='o', 
                label=f"Con Índice: {use_index}", linewidth=2)
plt.xlabel('Valor de Top-K')
plt.ylabel('Tiempo de Consulta Promedio (ms)')
plt.title('Rendimiento de Consulta por Valor de Top-K')
plt.legend()
plt.grid(True)

# 3. Speedup por tamaño de tabla
plt.subplot(2, 2, 3)
speedup_data = []
for size in table_sizes:
    no_idx_data = df[(df['table_size'] == size) & (df['index'] == 'No')]
    with_idx_data = df[(df['table_size'] == size) & (df['index'] == 'Yes')]
    
    if not no_idx_data.empty and not with_idx_data.empty:
        time_no_idx = no_idx_data['query_time_ms'].mean()
        time_with_idx = with_idx_data['query_time_ms'].mean()
        speedup = time_no_idx / time_with_idx
        speedup_data.append({'table_size': size, 'speedup': speedup})

if speedup_data:
    speedup_df = pd.DataFrame(speedup_data)
    plt.bar(np.arange(len(speedup_data)), speedup_df['speedup'], 
            tick_label=speedup_df['table_size'])
    plt.xlabel('Tamaño de Tabla (filas)')
    plt.ylabel('Aceleración (Tiempo Sin Índice / Tiempo Con Índice)')
    plt.title('Aceleración del Índice GIN por Tamaño de Tabla')
    plt.grid(True, axis='y')

# 4. Impacto de top-k en el speedup
plt.subplot(2, 2, 4)
top_k_speedup = []
for k in top_k_values:
    no_idx_data = df[(df['top_k'] == k) & (df['index'] == 'No')]
    with_idx_data = df[(df['top_k'] == k) & (df['index'] == 'Yes')]
    
    if not no_idx_data.empty and not with_idx_data.empty:
        time_no_idx = no_idx_data['query_time_ms'].mean()
        time_with_idx = with_idx_data['query_time_ms'].mean()
        speedup = time_no_idx / time_with_idx
        top_k_speedup.append({'top_k': k, 'speedup': speedup})

if top_k_speedup:
    top_k_speedup_df = pd.DataFrame(top_k_speedup)
    plt.bar(np.arange(len(top_k_speedup)), top_k_speedup_df['speedup'], 
            tick_label=top_k_speedup_df['top_k'])
    plt.xlabel('Valor de Top-K')
    plt.ylabel('Aceleración (Tiempo Sin Índice / Tiempo Con Índice)')
    plt.title('Impacto de Top-K en la Aceleración del Índice GIN')
    plt.grid(True, axis='y')

plt.tight_layout()
plt.savefig(os.path.join('performance', 'gin_index_performance.png'), dpi=300)
logging.info("Results visualizations saved to performance/gin_index_performance.png")

# Guardar resultados en CSV
df_all.to_csv(os.path.join('performance', 'gin_index_performance_results_all.csv'), index=False)
df.to_csv(os.path.join('performance', 'gin_index_performance_results.csv'), index=False)
logging.info("Detailed results saved to CSV files in performance/ folder")

# Análisis adicional: tiempo medio por tamaño y uso de índice
pivot_table = df.pivot_table(
    values='query_time_ms', 
    index='table_size',
    columns='index',
    aggfunc='mean'
)
pivot_table.to_csv(os.path.join('average_times', 'average_times_by_size.csv'))
logging.info("Average times by size saved to average_times/average_times_by_size.csv")

# Análisis adicional: tiempo medio por top-k y uso de índice
pivot_topk = df.pivot_table(
    values='query_time_ms', 
    index='top_k',
    columns='index',
    aggfunc='mean'
)
pivot_topk.to_csv(os.path.join('average_times', 'average_times_by_topk.csv'))
logging.info("Average times by top-k saved to average_times/average_times_by_topk.csv")

logging.info("Experiment completed successfully!")
conn.close()
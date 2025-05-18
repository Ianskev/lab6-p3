#!/usr/bin/env python
# filepath: c:\Users\Ian\Desktop\UTEC\CICLO 5\prueba2\analyze_plans.py

import os
import re
import pandas as pd
import matplotlib.pyplot as plt

# Create output directory for analysis
os.makedirs('performance', exist_ok=True)

# Función para extraer información relevante de los planes de ejecución
def parse_plan_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    # Extraer tiempo total de ejecución
    execution_time_match = re.search(r'Execution Time: ([0-9.]+) ms', content)
    execution_time = float(execution_time_match.group(1)) if execution_time_match else None
    
    # Verificar si se usó el índice GIN
    used_gin_index = 'Bitmap Index Scan on' in content and 'text_vector' in content
    
    # Extraer costo estimado
    planning_time_match = re.search(r'Planning Time: ([0-9.]+) ms', content)
    planning_time = float(planning_time_match.group(1)) if planning_time_match else None
    
    # Obtener información de tamaño, búsqueda y top-k del nombre del archivo
    parts = os.path.basename(filename).replace('.txt', '').split('_')
    size = int(parts[1])
    search_term = parts[2]
    top_k = int(parts[3])
    index_used = parts[4] == 'idxYes'
    
    return {
        'size': size,
        'search_term': search_term,
        'top_k': top_k,
        'index_used': index_used,
        'execution_time_ms': execution_time,
        'planning_time_ms': planning_time,
        'used_gin_index': used_gin_index
    }

# Analizar todos los archivos de plan
plans_dir = 'plans'
plan_files = [os.path.join(plans_dir, f) for f in os.listdir(plans_dir) if f.startswith('plan_') and f.endswith('.txt')]
plan_data = [parse_plan_file(f) for f in plan_files]
plan_df = pd.DataFrame(plan_data)

# Verificar que el índice se esté utilizando correctamente
index_verification = plan_df[['size', 'index_used', 'used_gin_index']]
print("Verificación de uso del índice GIN:")
print(index_verification)

# Comparación de tiempos de ejecución vs planificación
plt.figure(figsize=(12, 6))

for index_status in [True, False]:
    data = plan_df[plan_df['index_used'] == index_status]
    if not data.empty:
        # Ordenar datos por tamaño para asegurar que las líneas conecten correctamente
        data = data.sort_values('size')
        
        # Usar plot en lugar de scatter para conectar puntos con líneas
        plt.plot(data['size'], data['execution_time_ms'], 
                marker='o', linewidth=2, markersize=8,
                label=f"Ejecución {'con' if index_status else 'sin'} índice")
        
        plt.plot(data['size'], data['planning_time_ms'], 
                marker='x', linewidth=2, markersize=8, linestyle='--',
                label=f"Planificación {'con' if index_status else 'sin'} índice")

plt.xscale('log')
plt.yscale('log')
plt.xlabel('Tamaño de Tabla (filas)')
plt.ylabel('Tiempo (ms)')
plt.title('Tiempos de Ejecución y Planificación por Tamaño de Tabla')
plt.legend()
plt.grid(True)
plt.savefig(os.path.join('performance', 'execution_planning_times.png'), dpi=300)

print("Análisis de planes de ejecución completo. Resultados guardados en 'performance/execution_planning_times.png'")
import os
import pandas as pd

P_MAX_KW = 6.0
IRR_MAX = 1500
TEMP_MIN, TEMP_MAX = -10, 80

ruta_bronze = "data/bronze/telemetria.csv"
ruta_silver_dir = "data/silver"
ruta_silver_clean = os.path.join(ruta_silver_dir, "telemetria_clean.csv")
os.makedirs(ruta_silver_dir, exist_ok=True)

df = pd.read_csv(ruta_bronze)
filas_leidas = len(df)

for col in ["p_ac_kw", "irradiancia_wm2", "temp_modulo_c"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

mask_faltantes = df.isnull().any(axis=1)
rechazadas_faltantes = int(mask_faltantes.sum())
resto = df[~mask_faltantes]

mask_dup = resto.duplicated(subset=["ts", "dispositivo_id"], keep="first")
rechazadas_duplicados = int(mask_dup.sum())
resto = resto[~mask_dup]

mask_rango = (
    (resto["p_ac_kw"] < 0) | (resto["p_ac_kw"] > P_MAX_KW) |
    (resto["irradiancia_wm2"] < 0) | (resto["irradiancia_wm2"] > IRR_MAX) |
    (resto["temp_modulo_c"] < TEMP_MIN) | (resto["temp_modulo_c"] > TEMP_MAX)
)
rechazadas_rango = int(mask_rango.sum())
df_silver = resto[~mask_rango].copy()

filas_validas = len(df_silver)
filas_rechazadas_total = filas_leidas - filas_validas
pct_validas = (filas_validas / filas_leidas) * 100 if filas_leidas else 0.0

assert rechazadas_faltantes + rechazadas_duplicados + \
    rechazadas_rango == filas_rechazadas_total

df_silver.to_csv(ruta_silver_clean, index=False, encoding="utf-8")

print("=" * 50)
print("       REPORTE DE CALIDAD DE DATOS (SILVER)")
print("=" * 50)
print(f"Filas leídas (Bronze):            {filas_leidas}")
print(f"Rechazadas por datos faltantes:   {rechazadas_faltantes}")
print(f"Rechazadas por duplicados:        {rechazadas_duplicados}")
print(f"Rechazadas por rango inválido:    {rechazadas_rango}")
print("-" * 50)
print(f"Total filas rechazadas:           {filas_rechazadas_total}")
print(f"Total filas válidas (Silver):     {filas_validas}")
print(f"Porcentaje de datos válidos:      {pct_validas:.2f}%")
print("=" * 50)

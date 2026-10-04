# Solarbi-Gaitan-Mora

## Paso 3: carga a PostgreSQL

Desde la raíz del repositorio, instala las dependencias una vez:

```powershell
py -m pip install -r etl/requirements.txt
```

Configura la conexión en un archivo `.env` en la raíz del repositorio con esta línea (reemplaza el marcador por la contraseña; codifica los caracteres reservados de URL):

```dotenv
DATABASE_URL=postgresql://postgres.REF_DEL_PROYECTO:CLAVE@HOST_DEL_POOLER:5432/postgres
```

También puedes usar las variables `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` y `PGPASSWORD`. Ejecuta el ETL con un único comando:

```powershell
py etl/run_etl.py
```

El script crea `silver.lectura_5min` y `dwh.fact_energia_dia` si no existen. Usa `(ts, dispositivo)` y `(fecha, dispositivo)` como claves únicas y hace `UPSERT`; por ello, volverlo a ejecutar actualiza las mismas claves en vez de insertar duplicados. La energía diaria es la suma de `p_ac_kw * 5/60`. El porcentaje válido es el número de intervalos distintos recibidos sobre los 288 esperados en el día, expresado entre 0 y 100.

### Comprobación de idempotencia

Ejecuta `py etl/run_etl.py` dos veces y después corre `sql/02_verify_counts.sql` en ambas ocasiones. Los conteos de `silver.lectura_5min` y `dwh.fact_energia_dia` deben ser iguales en las dos consultas. `sql/01_create_tables.sql` contiene la definición de las tablas.

### Programación diaria

Expresión cron para ejecutar a medianoche:

```cron
0 0 * * * cd /ruta/al/Solarbi-Gaitan-Mora && /ruta/al/python etl/run_etl.py
```

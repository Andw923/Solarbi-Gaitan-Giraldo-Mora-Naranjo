# Solarbi-Gaitan-Mora

**Integrantes:** Andrew Gaitán Giraldo y Juan Diego Naranjo Mora
**Curso:** Inteligencia de Negocios · **Grupo:** 50 · **Periodo:** 2026-II · **Docente:** Ramiro Grisales Montoya

Trabajo de consulta que compara Power BI y Grafana sobre los mismos datos de una planta solar simulada (1 inversor de 5 kWp, 3 días, una lectura cada 5 minutos). Flujo: **Bronze** (crudo) → **Silver** (limpio con reglas de calidad) → **Gold** (resumen diario en PostgreSQL) → tableros en **Power BI** y **Grafana**.

## Estructura del repositorio

```
solarbi-apellido1-apellido2/
├── README.md
├── .gitignore
├── .env.example        plantilla de conexión (sin contraseña real)
├── docs/               PDF de la consulta y capturas
├── data/
│   ├── bronze/         telemetria.csv (crudo, no se modifica)
│   └── silver/         telemetria_clean.csv (limpio)
├── etl/                simulador.py, run_etl.py, requirements.txt
├── sql/                01_create_tables.sql, 02_verify_counts.sql
├── powerbi/            Solarbi.pbix
└── grafana/            dashboard_solarbi.json
```

## Paso 1: Bronze, datos crudos

`etl/simulador.py` genera `data/bronze/telemetria.csv`: 3 días de telemetría de un inversor de 5 kWp con anomalías inyectadas (potencia negativa, irradiancia faltante y filas duplicadas). El archivo de Bronze no se modifica después de generado. Los CSV ya vienen en el repositorio; si se regeneran, las cifras de este informe cambiarán.

## Paso 2: Silver, reglas de calidad

Se aplican tres reglas, en este orden y de modo que cada fila rechazada se cuente una sola vez:

1. **Datos faltantes:** filas con algún valor vacío.
2. **Duplicados:** filas repetidas para la misma marca de tiempo y dispositivo.
3. **Rango físico válido:** potencia y irradiancia no negativas y dentro de un máximo razonable; temperatura entre -10 y 80 °C.

| Concepto | Filas |
|---|---|
| Filas leídas (Bronze) | [ ] |
| Rechazadas por datos faltantes | [ ] |
| Rechazadas por duplicados | [ ] |
| Rechazadas por rango inválido | [ ] |
| **Filas válidas (Silver)** | [ ] |
| **Porcentaje de datos válidos** | [ ] % |

Resultado: `data/silver/telemetria_clean.csv`.

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

<!-- PEGAR AQUÍ, SIN CAMBIOS, EL RESTO DEL PASO 3 DEL COMPAÑERO (desde el comando del ETL en adelante) -->

### Configuración de la conexión (elegir una opción)

El repositorio no incluye contraseñas. Quien ejecute el proyecto debe crear su propio `.env` a partir de la plantilla:

```powershell
Copy-Item .env.example .env
```

(en Linux o macOS: `cp .env.example .env`). Luego abrir `.env`, dejar **una sola** línea `DATABASE_URL` sin `#` y reemplazar `CLAVE`:

- **Opción A, base en la nube:** requiere las credenciales de la base alojada del equipo; sin ellas esta opción no conecta.
- **Opción B, PostgreSQL instalado en el equipo (recomendada para reproducir):**
  1. Instalar PostgreSQL con pgAdmin 4 y verificar que el servicio esté en ejecución (`services.msc`).
  2. En pgAdmin: clic derecho en *Databases* → *Create* → *Database* → nombre `solarbi`. El ETL crea los esquemas y las tablas, pero **no** la base.
  3. Dejar activa la línea `DATABASE_URL=postgresql://postgres:CLAVE@localhost:5432/solarbi` con la contraseña propia. Si tiene caracteres especiales, se codifican (`@` es `%40`, `#` es `%23`).

Para comprobar, ejecutar `py etl/run_etl.py`: debe terminar con "Carga completada…". Después, correr `sql/02_verify_counts.sql` en pgAdmin. Silver tiene una fila por lectura de 5 minutos y Gold una por día y dispositivo, así que los dos conteos no son iguales entre sí. Lo que se compara es:

- `silver.lectura_5min` con las **filas válidas** del reporte del Paso 2.
- `dwh.fact_energia_dia` con **días × dispositivos**.

| Síntoma | Causa y solución |
|---|---|
| "Configura DATABASE_URL…" | El `.env` no está en la raíz, está mal nombrado (por ejemplo `.env.txt`) o está vacío |
| "connection refused" o "timeout" | El servicio de PostgreSQL está apagado |
| `database "solarbi" does not exist` | Falta crear la base (Opción B, paso 2) |
| `password authentication failed` | La contraseña del `.env` no coincide con la de PostgreSQL |
| "No existe el CSV limpio" | Falta el paso de limpieza o el CSV no está en `data/silver/` |

### Qué crea la carga

- `silver.lectura_5min`: lecturas limpias de 5 minutos.
- `dwh.fact_energia_dia`: resumen diario por dispositivo (`fecha`, `dispositivo`, `energia_kwh`, `pct_datos_validos`).
- La energía de cada intervalo es la potencia (kW) × 5/60 de hora.
- Las tablas se definen en `sql/01_create_tables.sql`, que el ETL ejecuta solo.

### Carga idempotente

La carga usa `INSERT … ON CONFLICT DO UPDATE`, así que repetirla no duplica datos. Prueba (ejecutar el ETL dos veces y consultar `sql/02_verify_counts.sql` después de cada una):

| Ejecución | `silver.lectura_5min` | `dwh.fact_energia_dia` |
|---|---|---|
| 1.ª | [ ] | [ ] |
| 2.ª | [ ] | [ ] |

### Programación diaria a medianoche (propuesta, no implementada)

- Linux/macOS (cron):

```
0 0 * * * cd /ruta/al/proyecto && python etl/run_etl.py >> etl.log 2>&1
```

- Windows (Programador de tareas):

```powershell
schtasks /Create /SC DAILY /ST 00:00 /TN "SolarBI_ETL" /TR "python C:\ruta\al\proyecto\etl\run_etl.py"
```

## Paso 4: Power BI

**Conexión:** *Obtener datos* → *Base de datos PostgreSQL* → modo **Importar**. En nuestra entrega: servidor `localhost`, base `solarbi` (instalación local); con una base alojada se cambian servidor y base. Tablas cargadas: `dwh.fact_energia_dia` y `silver.lectura_5min`. El `.pbix` ya trae los datos; para actualizar pide la contraseña propia.

**Parámetro de tarifa:** *Modelado* → *Nuevo parámetro* → `Tarifa COP kWh` (rango numérico, con segmentación en la página).

**Medidas DAX** (todas las cifras de la página salen de ellas):

```
Energía kWh = SUM(fact_energia_dia[energia_kwh])

Capacidad kWp = 5 * DISTINCTCOUNT(fact_energia_dia[dispositivo])

Yield kWh/kWp = DIVIDE([Energía kWh], [Capacidad kWp])

Ahorro COP = [Energía kWh] * 'Tarifa COP kWh'[Tarifa COP kWh Value]

% Datos válidos = AVERAGE(fact_energia_dia[pct_datos_validos])
```

**Página:** tarjeta con el yield (kWh/kWp), gráfico de columnas con la energía diaria y tarjeta con el ahorro estimado en COP. Al mover la tarifa solo cambia el ahorro; la energía y el yield no dependen de ella.


**Fuente de la tarifa:** EPM, "Tarifas y costo de energía eléctrica, mercado regulado", [mes y año], [categoría usada], [valor] $/kWh. Consultado el [fecha]. Fuente: epm.com.co → Clientes y usuarios → Energía → Tarifas de energía.

<!-- PEGAR AQUÍ, SIN CAMBIOS, TODA LA SECCIÓN DE GRAFANA DEL COMPAÑERO (Paso 5). El dashboard exportado está en grafana/dashboard_solarbi.json -->

## Quién hizo qué

| Parte | Responsable |
|---|---|
| Simulador y datos Bronze | [Andrew Gaitán Giraldo] |
| Reglas de calidad y reporte (Silver) | [Andrew Gaitán Giraldo] |
| Carga a PostgreSQL y scripts SQL (Gold) | [ ] |
| Dashboard de Power BI y fuente de la tarifa | [Andrew Gaitán Giraldo] |
| Dashboard de Grafana | [ ] |
| README y PDF de la consulta | [Andrew Gaitán Giraldo - Juan Diego Naranjo Mora] |

Este repositorio es la base de los siguientes trabajos del proyecto durante el semestre.

## Paso 5: Grafana

El dashboard está en `grafana/dashboard_solarbi.json`. En Grafana OSS, agrega una fuente de datos **PostgreSQL** y copia los datos de **Supabase → Connect → Session pooler**: host y puerto del pooler, base `postgres`, usuario `postgres.<REF_DEL_PROYECTO>` y la contraseña actual. Configura SSL en modo `require` y usa **Save & test**.

Luego importa `grafana/dashboard_solarbi.json` desde **Dashboards → New → Import** y selecciona esa fuente PostgreSQL cuando Grafana lo solicite. El tablero contiene la variable `dispositivo`, cuatro indicadores (cobertura, energía total, lecturas válidas y potencia pico), una serie temporal de irradiancia y potencia con `$__timeFilter(ts)`, energía diaria y calidad diaria. El indicador de calidad usa umbrales. El rango inicial cubre las fechas de los datos de ejemplo (5–7 de octubre de 2026); se puede cambiar desde el selector de tiempo.

Después de importar y comprobarlo en Grafana, pueden exportar desde **Dashboard → Export → Export as code** y guardar el JSON descargado en el mismo archivo del repositorio. La fuente de datos guarda su contraseña en Grafana; el JSON del dashboard solo conserva una referencia a esa fuente.

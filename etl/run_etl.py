"""Carga idempotente del CSV limpio a PostgreSQL (Silver y Gold)."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
CLEAN_CSV = ROOT / "data" / "silver" / "telemetria_clean.csv"
DDL = ROOT / "sql" / "01_create_tables.sql"
INTERVAL_HOURS = 5 / 60
INTERVALOS_DIA = 24 * 60 // 5


def build_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Resume energía y porcentaje de intervalos observados por día/dispositivo."""
    work = df.copy()
    work["ts"] = pd.to_datetime(work["ts"], errors="raise")
    work["dispositivo_id"] = pd.to_numeric(work["dispositivo_id"], errors="raise").astype(int)
    work["p_ac_kw"] = pd.to_numeric(work["p_ac_kw"], errors="raise")
    work["fecha"] = work["ts"].dt.date
    work["energia_kwh"] = work["p_ac_kw"] * INTERVAL_HOURS
    daily = work.groupby(["fecha", "dispositivo_id"], as_index=False).agg(
        energia_kwh=("energia_kwh", "sum"),
        intervalos_validos=("ts", "nunique"),
    )
    daily["pct_datos_validos"] = (
        daily["intervalos_validos"].clip(upper=INTERVALOS_DIA) / INTERVALOS_DIA * 100
    ).round(2)
    return daily[["fecha", "dispositivo_id", "energia_kwh", "pct_datos_validos"]]


def main() -> None:
    load_dotenv(ROOT / ".env")
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        # Alternativa sin URL: PGHOST, PGPORT, PGDATABASE, PGUSER y PGPASSWORD.
        required = ("PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            raise SystemExit("Configura DATABASE_URL o estas variables: " + ", ".join(missing))
        dsn = " ".join(
            f"{key}={os.environ[key]}"
            for key in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD")
            if os.environ.get(key)
        )

    if not CLEAN_CSV.exists():
        raise SystemExit(f"No existe el CSV limpio: {CLEAN_CSV}. Ejecuta primero el paso de limpieza.")
    readings = pd.read_csv(CLEAN_CSV)
    required_cols = {"ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"}
    if not required_cols.issubset(readings.columns):
        raise SystemExit(f"Al CSV le faltan columnas: {sorted(required_cols - set(readings.columns))}")
    readings["ts"] = pd.to_datetime(readings["ts"], errors="raise")
    for col in ("dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"):
        readings[col] = pd.to_numeric(readings[col], errors="raise")
    readings["dispositivo_id"] = readings["dispositivo_id"].astype(int)
    if readings.duplicated(["ts", "dispositivo_id"]).any():
        raise SystemExit("El CSV contiene duplicados para (ts, dispositivo_id).")
    daily = build_daily(readings)

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL.read_text(encoding="utf-8"))
            execute_values(
                cur,
                """INSERT INTO silver.lectura_5min
                   (ts, dispositivo, p_ac_kw, irradiancia_wm2, temp_modulo_c) VALUES %s
                   ON CONFLICT (ts, dispositivo) DO UPDATE SET
                     p_ac_kw = EXCLUDED.p_ac_kw,
                     irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
                     temp_modulo_c = EXCLUDED.temp_modulo_c""",
                [tuple(row) for row in readings[["ts", "dispositivo_id", "p_ac_kw", "irradiancia_wm2", "temp_modulo_c"]].itertuples(index=False, name=None)],
                page_size=1000,
            )
            execute_values(
                cur,
                """INSERT INTO dwh.fact_energia_dia
                   (fecha, dispositivo, energia_kwh, pct_datos_validos) VALUES %s
                   ON CONFLICT (fecha, dispositivo) DO UPDATE SET
                     energia_kwh = EXCLUDED.energia_kwh,
                     pct_datos_validos = EXCLUDED.pct_datos_validos""",
                [tuple(row) for row in daily.itertuples(index=False, name=None)],
                page_size=1000,
            )
            cur.execute("SELECT COUNT(*) FROM silver.lectura_5min")
            silver_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM dwh.fact_energia_dia")
            fact_count = cur.fetchone()[0]
    print(f"Carga completada: CSV={len(readings)}, Silver total={silver_count}, Gold total={fact_count}")


if __name__ == "__main__":
    main()

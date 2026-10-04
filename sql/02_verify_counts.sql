-- Ejecutar después de cada carga; los dos resultados deben coincidir.
SELECT 'silver.lectura_5min' AS tabla, COUNT(*) AS filas FROM silver.lectura_5min
UNION ALL
SELECT 'dwh.fact_energia_dia', COUNT(*) FROM dwh.fact_energia_dia;

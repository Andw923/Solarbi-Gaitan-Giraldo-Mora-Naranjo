-- Estructura Gold: se puede ejecutar varias veces sin alterar los datos.
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS dwh;

CREATE TABLE IF NOT EXISTS silver.lectura_5min (
    ts              TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    dispositivo     INTEGER NOT NULL,
    p_ac_kw         NUMERIC(10, 4) NOT NULL,
    irradiancia_wm2 NUMERIC(10, 2) NOT NULL,
    temp_modulo_c   NUMERIC(8, 2) NOT NULL,
    CONSTRAINT pk_lectura_5min PRIMARY KEY (ts, dispositivo)
);

CREATE TABLE IF NOT EXISTS dwh.fact_energia_dia (
    fecha              DATE NOT NULL,
    dispositivo        INTEGER NOT NULL,
    energia_kwh        NUMERIC(14, 6) NOT NULL,
    pct_datos_validos  NUMERIC(5, 2) NOT NULL,
    CONSTRAINT pk_fact_energia_dia PRIMARY KEY (fecha, dispositivo),
    CONSTRAINT ck_pct_datos_validos CHECK (pct_datos_validos BETWEEN 0 AND 100)
);

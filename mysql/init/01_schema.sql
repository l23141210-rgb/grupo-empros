-- =====================================================
-- GRUPO EMPROS - Schema profesional
-- =====================================================

USE grupo_empros;

CREATE TABLE IF NOT EXISTS usuarios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL,
    usuario         VARCHAR(60)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    rol             ENUM('administrador', 'empleado') NOT NULL DEFAULT 'empleado',
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS productos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    codigo          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NOT NULL,
    categoria       VARCHAR(100) NULL,
    unidad          VARCHAR(30)  NULL,
    almacen         VARCHAR(100) NULL,
    stock_actual    INT          NOT NULL DEFAULT 0,
    stock_minimo    INT          NOT NULL DEFAULT 0,
    stock_maximo    INT          NOT NULL DEFAULT 0,
    precio_venta    DECIMAL(12,2) NULL DEFAULT 0,
    observaciones   TEXT         NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_categoria (categoria),
    INDEX idx_stock (stock_actual)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS movimientos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    producto_id     INT          NOT NULL,
    tipo            ENUM('entrada', 'salida') NOT NULL,
    cantidad        INT          NOT NULL,
    responsable_id  INT          NULL,
    observaciones   TEXT         NULL,
    origen          ENUM('manual', 'compra_web', 'ajuste') NOT NULL DEFAULT 'manual',
    fecha           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT,
    FOREIGN KEY (responsable_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_fecha (fecha),
    INDEX idx_tipo (tipo)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS estadisticas_semanales (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    anio                INT          NOT NULL,
    semana              INT          NOT NULL,
    fecha_inicio        DATE         NOT NULL,
    fecha_fin           DATE         NOT NULL,
    total_piezas        INT          NOT NULL DEFAULT 0,
    piezas_entradas     INT          NOT NULL DEFAULT 0,
    piezas_salidas      INT          NOT NULL DEFAULT 0,
    piezas_vendidas     INT          NOT NULL DEFAULT 0,
    valor_inventario    DECIMAL(14,2) NOT NULL DEFAULT 0,
    productos_bajo_min  INT          NOT NULL DEFAULT 0,
    generado_en         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_anio_semana (anio, semana)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reportes_pdf (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    tipo            ENUM('semanal', 'quincenal', 'mensual') NOT NULL,
    periodo         VARCHAR(50)  NOT NULL,
    archivo         VARCHAR(255) NOT NULL,
    generado_por    INT          NULL,
    enviado        TINYINT(1)   NOT NULL DEFAULT 0,
    fecha_envio     DATETIME     NULL,
    creado_en       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB;

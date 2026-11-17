"""Servicio de estadísticas semanales de inventario."""
from datetime import datetime, timedelta, date
from config import conectar_db


def _semana_actual():
    hoy = date.today()
    inicio = hoy - timedelta(days=hoy.weekday())  # Lunes
    fin = inicio + timedelta(days=6)
    anio, semana, _ = hoy.isocalendar()
    return anio, semana, inicio, fin


def obtener_resumen_periodo(fecha_inicio, fecha_fin):
    """Resumen de movimientos y stock entre dos fechas."""
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        # Stock actual total
        cursor.execute("""
            SELECT
                COUNT(*) AS total_productos,
                COALESCE(SUM(stock_actual), 0) AS total_piezas,
                COALESCE(SUM(stock_actual * COALESCE(precio_venta, 0)), 0) AS valor_estimado,
                SUM(CASE WHEN stock_actual < stock_minimo THEN 1 ELSE 0 END) AS bajo_minimo
            FROM productos
            WHERE activo = 1
        """)
        stock = cursor.fetchone()

        # Movimientos del periodo
        cursor.execute("""
            SELECT
                tipo,
                COALESCE(SUM(cantidad), 0) AS total,
                origen
            FROM movimientos
            WHERE fecha BETWEEN %s AND %s
            GROUP BY tipo, origen
        """, (fecha_inicio, fecha_fin + timedelta(days=1)))
        movs = cursor.fetchall()

        entradas = sum(m["total"] for m in movs if m["tipo"] == "entrada")
        salidas = sum(m["total"] for m in movs if m["tipo"] == "salida")
        vendidas = sum(
            m["total"] for m in movs
            if m["tipo"] == "salida" and m.get("origen") == "compra_web"
        )

        return {
            "total_productos": stock["total_productos"] or 0,
            "total_piezas": int(stock["total_piezas"] or 0),
            "valor_estimado": float(stock["valor_estimado"] or 0),
            "bajo_minimo": int(stock["bajo_minimo"] or 0),
            "entradas": int(entradas),
            "salidas": int(salidas),
            "vendidas": int(vendidas),
        }
    finally:
        cursor.close()
        conexion.close()


def productos_bajo_minimo():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, codigo, descripcion, stock_actual, stock_minimo, categoria
            FROM productos
            WHERE activo = 1 AND stock_actual < stock_minimo
            ORDER BY (stock_minimo - stock_actual) DESC
            LIMIT 50
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()


def ultimos_movimientos(limit=30, fecha_inicio=None, fecha_fin=None):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        sql = """
            SELECT m.id, m.tipo, m.cantidad, m.fecha, m.origen,
                   p.codigo, p.descripcion,
                   u.nombre AS responsable
            FROM movimientos m
            JOIN productos p ON p.id = m.producto_id
            LEFT JOIN usuarios u ON u.id = m.responsable_id
        """
        params = []
        if fecha_inicio and fecha_fin:
            sql += " WHERE m.fecha BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin + timedelta(days=1)])
        sql += " ORDER BY m.fecha DESC LIMIT %s"
        params.append(limit)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()


def generar_snapshot_semanal():
    """Crea o actualiza el snapshot de la semana actual."""
    anio, semana, inicio, fin = _semana_actual()
    resumen = obtener_resumen_periodo(inicio, fin)

    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO estadisticas_semanales
                (anio, semana, fecha_inicio, fecha_fin,
                 total_piezas, piezas_entradas, piezas_salidas,
                 piezas_vendidas, valor_inventario, productos_bajo_min)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                total_piezas = VALUES(total_piezas),
                piezas_entradas = VALUES(piezas_entradas),
                piezas_salidas = VALUES(piezas_salidas),
                piezas_vendidas = VALUES(piezas_vendidas),
                valor_inventario = VALUES(valor_inventario),
                productos_bajo_min = VALUES(productos_bajo_min),
                generado_en = CURRENT_TIMESTAMP
        """, (
            anio, semana, inicio, fin,
            resumen["total_piezas"],
            resumen["entradas"],
            resumen["salidas"],
            resumen["vendidas"],
            resumen["valor_estimado"],
            resumen["bajo_minimo"],
        ))
        conexion.commit()
        return True
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def historial_semanas(limit=12):
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT *
            FROM estadisticas_semanales
            ORDER BY anio DESC, semana DESC
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

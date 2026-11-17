# Grupo Empros — Sistema de Inventarios

## Arrancar con Docker

```bash
cd grupo_empros
docker compose up --build
```

Abre: **http://localhost:5001**

### Credenciales iniciales

- Usuario: `admin`
- Contraseña: `AdminEmpros2026!`

(Se crea automáticamente la primera vez que arranca.)

## Qué incluye esta versión

- Diseño profesional (sidebar + dashboard)
- Roles: **Administrador** (todo) y **Empleado** (solo lectura)
- Control estadístico semanal + historial
- Generación y descarga de PDF (semanal / quincenal / mensual)
- Gestión de empleados (crear usuarios)
- Todo en contenedores Docker (MySQL + Flask)

## Próximos módulos (pendientes)

- Página web pública (catálogo + WhatsApp)
- Aplicación de compras online (carrito + pago tarjeta + descuento inventario)
- Logo de la empresa

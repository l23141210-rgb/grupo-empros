# Grupo Empros — Sistema de Inventarios

Aplicación web desarrollada mediante una arquitectura de microservicios utilizando Docker, MySQL y Python.

## 1. Estructura del proyecto

- `catalog/`: Microservicio de catálogo.
- `inventory/`: Microservicio de inventario.
- `mysql/`: Archivos de inicialización de MySQL.
- `docker-compose.yml`: Configuración de Docker.
- `importar_excel.py`: Script para importar información.
- `.env.example`: Plantilla de variables de entorno.

## 2. Tecnologías utilizadas

- Python
- Flask
- MySQL 8.0
- Docker
- Docker Compose
- Git
- GitHub

## 3. Características del sistema

- Diseño profesional con menú lateral y dashboard.
- Roles de usuario: Administrador y Empleado.
- Control estadístico semanal e historial.
- Generación y descarga de reportes PDF.
- Reportes semanales, quincenales y mensuales.
- Gestión de empleados y creación de usuarios.
- Microservicios de catálogo e inventario.
- Base de datos MySQL.

## 4. Requisitos

- Git instalado.
- Docker Desktop instalado y ejecutándose.
- Docker Compose disponible.

## 5. Descargar el proyecto

Clonar el repositorio:

```bash
git clone https://github.com/l23141210-rgb/grupo-empros.git
```

Entrar a la carpeta:

```bash
cd grupo-empros
```

## 6. Configurar las variables de entorno

Crear el archivo `.env`:

En PowerShell:

```powershell
Copy-Item .env.example .env
```

Editar el archivo `.env` y colocar las credenciales necesarias para ejecutar la aplicación.

No compartir el archivo `.env` ni publicar contraseñas reales.

## 7. Ejecutar el proyecto

Construir e iniciar los servicios:

```bash
docker compose up -d --build
```

## 8. Acceso a los servicios

**Inventario:**

http://localhost:5001

**Catálogo:**

http://localhost:5004

**Base de datos:**

Puerto 3307.

## 9. Verificar los contenedores

Consultar los contenedores activos:

```bash
docker compose ps
```

Consultar registros:

```bash
docker compose logs --tail=50
```

## 10. Detener los servicios

```bash
docker compose down
```

## 11. Arquitectura del sistema

Los microservicios de catálogo e inventario utilizan una base de datos MySQL compartida mediante la red interna de Docker Compose.

Cada servicio tiene responsabilidades específicas para facilitar el mantenimiento, organización y escalabilidad de la aplicación.

## 12. Próximos módulos

- Página web pública (catálogo y WhatsApp).
- Aplicación de compras en línea.
- Carrito de compras y pagos con tarjeta.
- Descuento automático de
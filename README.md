

\# GRUPO EMPROS



Aplicación web desarrollada mediante una arquitectura

de microservicios utilizando Docker, MySQL y Python.



\## 1. Estructura del proyecto



\- catalog/: Microservicio de catálogo.

\- inventory/: Microservicio de inventario.

\- mysql/: Archivos de inicialización de MySQL.

\- docker-compose.yml: Configuración de Docker.

\- importar\_excel.py: Script para importar información.

\- .env.example: Plantilla de variables de entorno.



\## 2. Tecnologías utilizadas



\- Python

\- Flask

\- MySQL 8.0

\- Docker

\- Docker Compose

\- Git

\- GitHub



\## 3. Requisitos



\- Git instalado.

\- Docker Desktop instalado y ejecutándose.

\- Docker Compose disponible.



\## 4. Descargar el proyecto



Clonar el repositorio:



git clone https://github.com/USUARIO/grupo-empros.git



Entrar a la carpeta:



cd grupo-empros



\## 5. Configurar las variables de entorno



Crear el archivo .env:



Copy-Item .env.example .env



Editar el archivo .env y colocar las credenciales

necesarias para ejecutar la aplicación.



No compartir el archivo .env.



\## 6. Ejecutar el proyecto



Construir e iniciar los servicios:



docker compose up -d --build



\## 7. Acceso a los servicios



Inventario:

http://localhost:5001



Catálogo:

http://localhost:5004



Base de datos:

Puerto 3307.



\## 8. Verificar los contenedores



docker compose ps



Consultar registros:



docker compose logs --tail=50



\## 9. Detener los servicios



docker compose down



\## 10. Arquitectura



Los microservicios de catálogo e inventario

utilizan una base de datos MySQL compartida

mediante la red interna de Docker Compose.




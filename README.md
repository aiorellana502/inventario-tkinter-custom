# Sistema de Inventario con Python, Tkinter Custom y Escaneo de Códigos de Barras

Este proyecto es una aplicación de escritorio para la gestión de inventario, desarrollada en Python utilizando [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) para la interfaz gráfica. Permite agregar productos, registrar importaciones, escanear códigos de barras usando la cámara y exportar datos a Excel.

## Características principales

- **Gestión de productos**: Agrega, edita y busca productos por código de barras.
- **Importaciones**: Registra entradas de inventario, cantidades aceptadas y rechazadas, lote y fecha de expiración.
- **Escaneo de códigos de barras**: Usa la cámara del equipo para leer códigos de barras de manera rápida.
- **Exportación a Excel**: Exporta las importaciones registradas a un archivo Excel.
- **Eliminación segura de datos**: Borra todos los datos de productos e importaciones con confirmación y contraseña.
- **Edición y eliminación de importaciones**: Permite modificar y eliminar registros de importaciones ya existentes.
- **Ventanas modales y control de cierres**: Evita el cierre accidental cuando hay ventanas hijas abiertas.

## Requisitos

- Python 3.8 o superior
- Paquetes Python (ver `requirements.txt`)
- En sistemas Linux, puede requerir la instalación de `libzbar0` para el soporte de escaneo de códigos de barras:
  ```bash
  sudo apt-get install libzbar0
  ```

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/aiorellana502/inventario-tkinter-custom.git
   cd inventario-tkinter-custom
   ```

2. (Opcional) Crea y activa un entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Ejecuta la aplicación principal:
   ```bash
   python inventario_tkintercustom.py
   ```

2. Sigue las instrucciones en pantalla para agregar productos, registrar importaciones y usar las funciones del sistema.

## Estructura de archivos

- `inventario_tkintercustom.py` — Código fuente principal de la aplicación.
- `productos.db` — Base de datos SQLite generada automáticamente al ejecutar la app.
- `requirements.txt` — Lista de dependencias Python.
- `.gitignore` — Archivos y carpetas ignorados por git.

## Personalización

- Puedes cambiar la contraseña de borrado total modificando la variable `DELETE_PASSWORD` en el código fuente.
- Para cambiar el nombre de la base de datos, edita la variable `DB_NAME`.

## Notas

- Si tienes más de una cámara conectada, puedes modificar el índice de la cámara en el código para el escaneo de códigos de barras.
- Los archivos de base de datos (`productos.db`) y las exportaciones de Excel no se suben al repositorio por defecto.

## Licencia

MIT
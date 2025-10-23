# Instrucciones para subir el proyecto a GitHub

## Opción 1: Usando el script automatizado (RECOMENDADO)

1. Abre PowerShell como administrador
2. Navega al directorio del proyecto:
   ```
   cd "C:\Users\Usuario\Desktop\Top_NoT\Ste"
   ```
3. Ejecuta el script:
   ```
   .\deploy_to_github.ps1
   ```
4. Sigue las instrucciones del script

## Opción 2: Manual (si el script no funciona)

### Paso 1: Crear repositorio en GitHub
1. Ve a [GitHub](https://github.com) e inicia sesión
2. Haz clic en "New repository" o ve a https://github.com/new
3. Nombra tu repositorio (ejemplo: "visor-partidos-streamlit")
4. Marca como público si quieres usar Streamlit Cloud gratuito
5. NO inicialices con README, .gitignore, o licencia (ya los tienes)
6. Haz clic en "Create repository"

### Paso 2: Configurar Git localmente
1. Abre PowerShell en el directorio del proyecto
2. Configura tu identidad (solo si es la primera vez):
   ```
   git config --global user.name "Tu Nombre"
   git config --global user.email "tu-email@ejemplo.com"
   ```

### Paso 3: Subir el proyecto
1. Si no has inicializado Git:
   ```
   git init
   git branch -M main
   ```
2. Agregar archivos:
   ```
   git add .
   git commit -m "Actualización del proyecto de visor de partidos"
   ```
3. Conectar con GitHub (reemplaza TU-USUARIO y TU-REPOSITORIO):
   ```
   git remote add origin https://github.com/TU-USUARIO/TU-REPOSITORIO.git
   git push -u origin main
   ```

## Paso 3: Desplegar en Streamlit Cloud

1. Ve a [Streamlit Cloud](https://streamlit.io/cloud)
2. Inicia sesión con tu cuenta de GitHub
3. Haz clic en "New app"
4. Selecciona tu repositorio de GitHub
5. Configura:
   - **Repository**: tu-usuario/tu-repositorio
   - **Branch**: main
   - **Main file path**: streamlit_app_final.py
6. Haz clic en "Deploy"
7. Espera a que se complete la instalación (puede tomar varios minutos)

## Archivos importantes incluidos

- `streamlit_app_final.py` - Aplicación principal
- `requirements.txt` - Dependencias de Python
- `data.json` - Datos de partidos
- `Descarga_Todo/` - Módulos auxiliares
- `.streamlit/config.toml` - Configuración de Streamlit
- `.gitignore` - Archivos a ignorar
- `README.md` - Documentación

## Solución de problemas

### Si Git no está instalado:
- El script intentará instalarlo automáticamente
- O descárgalo manualmente de https://git-scm.com/

### Si tienes problemas de autenticación:
- Usa un token personal de GitHub en lugar de contraseña
- Ve a GitHub > Settings > Developer settings > Personal access tokens

### Si Streamlit Cloud falla:
- Verifica que todos los archivos estén en el repositorio
- Revisa que `requirements.txt` tenga todas las dependencias
- Comprueba los logs en Streamlit Cloud para errores específicos

### Si faltan módulos:
- Asegúrate de que la carpeta `Descarga_Todo` esté completa
- Verifica que `data.json` esté en el directorio raíz
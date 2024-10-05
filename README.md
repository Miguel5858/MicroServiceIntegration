
## Paso 1: Crear el `Dockerfile`

1. **Crear el archivo Dockerfile**:
   - En la raíz de tu proyecto, crea un archivo llamado `Dockerfile`. Este archivo será responsable de definir cómo se construye la imagen de tu aplicación Flask.

2. **Definir la imagen base**:
   - Usé `FROM python:3.9-slim` para obtener una imagen base ligera de Python 3.9. Esto asegura que tengamos el entorno adecuado para ejecutar nuestra aplicación.

3. **Configurar el directorio de trabajo**:
   - Agregué `WORKDIR /app`, que establece el directorio de trabajo donde se ejecutarán los comandos siguientes.

4. **Copiar los archivos necesarios**:
   - Usé `COPY requirements.txt ./` y `COPY . .` para copiar el archivo de requisitos y el resto de la aplicación al contenedor.

5. **Instalar dependencias**:
   - Incluí `RUN pip install --no-cache-dir -r requirements.txt` para instalar las bibliotecas necesarias definidas en el archivo `requirements.txt`.

6. **Exponer el puerto**:
   - Utilicé `EXPOSE 4000` para indicar que la aplicación escuchará en el puerto 4000.

7. **Definir el comando de inicio**:
   - Finalmente, añadí `CMD ["python", "consumer.py"]` para especificar el comando que se ejecutará al iniciar el contenedor.

   El contenido completo del `Dockerfile` se ve así:

   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app

   # Copia los archivos necesarios
   COPY requirements.txt ./
   COPY . .

   # Instalar dependencias
   RUN pip install --no-cache-dir -r requirements.txt

   # Exponer el puerto
   EXPOSE 4000

   # Comando para ejecutar la aplicación
   CMD ["python", "consumer.py"]

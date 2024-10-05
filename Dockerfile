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

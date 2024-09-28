import pika
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from flask import Flask, render_template
import threading

# Configuración de SQLAlchemy para MySQL (sin contraseña)
DATABASE_URL = 'mysql+pymysql://root@localhost:3306/saleQueuedb'

engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Definir la tabla de facturas (invoices)
class Invoice(Base):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(CHAR(36), nullable=False)  # Usar CHAR(36) para UUID en MySQL
    sale_date = Column(DateTime, nullable=False)
    invoice_number = Column(String(255), nullable=False)  # Especificar longitud para VARCHAR
    payment_method = Column(String(255), nullable=False)  # Especificar longitud para VARCHAR
    total_sale = Column(Float, nullable=False)
    status = Column(Boolean, nullable=False)

# Crear las tablas en la base de datos
Base.metadata.create_all(engine)

# Crear una sesión
Session = sessionmaker(bind=engine)

# Inicializar Flask
app = Flask(__name__)

@app.route('/')
def index():
    # Crear una sesión para consultar las facturas
    session = Session()
    invoices = session.query(Invoice).all()  # Obtener todas las facturas
    session.close()
    
    return render_template('facturas.html', invoices=invoices)

# Credenciales para conectarse a RabbitMQ
credentials = pika.PlainCredentials('admin', 'admin')

# Conectar al servidor RabbitMQ con credenciales
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='localhost',  # Cambia 'localhost' si el contenedor está en otra máquina
    credentials=credentials
))

channel = connection.channel()

# Declarar la cola (debe ser la misma que ya esté declarada en el servidor)
channel.queue_declare(queue='saleQueue')

# Función de callback que se ejecutará cada vez que un mensaje sea recibido
def callback(ch, method, properties, body):
    # El mensaje recibido (en formato JSON)
    message = body.decode()
    print(f" [x] Recibido: {message}")

    # Convertir el mensaje JSON a un diccionario de Python
    data = json.loads(message)

    # Convertir la fecha usando datetime.strptime y luego formatearla correctamente
    sale_date = datetime.strptime(data['SaleDate'], "%Y-%m-%dT%H:%M:%S.%fZ")

    # Crear una nueva factura y guardarla en la base de datos
    invoice = Invoice(
        customer_id=data['CustomerId'],
        sale_date=sale_date,
        invoice_number=data['InvoiceNumber'],
        payment_method=data['PaymentMethod'],
        total_sale=data['TotalSale'],
        status=data['Status']  # MySQL acepta True y False para el tipo Boolean
    )

    session = Session()  # Crear una nueva sesión para guardar la factura
    session.add(invoice)
    session.commit()
    session.close()  # Cerrar la sesión después de guardar
    print(f" [x] Factura guardada en la base de datos: {data}")

# Consumir mensajes de la cola
channel.basic_consume(queue='saleQueue', on_message_callback=callback, auto_ack=True)

# Función para ejecutar el consumidor en un hilo separado
def run_consumer():
    print(' [*] Esperando mensajes. Para salir presiona CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    # Iniciar el hilo del consumidor
    consumer_thread = threading.Thread(target=run_consumer)
    consumer_thread.start()

    # Iniciar el servidor Flask
    app.run(debug=True, use_reloader=False)  # use_reloader=False para evitar múltiples instancias

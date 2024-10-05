import pika
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from flask import Flask, render_template
import threading
import signal
import sys
import time

# Configuración de SQLAlchemy para MySQL
# DATABASE_URL = 'mysql+pymysql://root:admin@database-mysql:3306/saleQueuedb'
DATABASE_URL = 'mysql+pymysql://root:admin@database-mysql:3306/saleQueuedb'


engine = create_engine(DATABASE_URL)
Base = declarative_base()

while True:
    try:
        with engine.connect() as connection:
            # Ejecutar una simple consulta para comprobar la conexión
            connection.execute("SELECT 1")
        break  # Salir del bucle si la conexión fue exitosa
    except Exception as e:
        print(f"Esperando a que la base de datos esté lista... {e}")
        time.sleep(5)

# Crear la base de datos si no existe
try:
    with engine.connect() as connection:
        connection.execute("CREATE DATABASE IF NOT EXISTS saleQueuedb")
        print("Base de datos 'saleQueuedb' creada o ya existe.")
except Exception as e:
    print(f"Error al crear la base de datos: {e}")

# Definir la tabla de facturas (invoices)
class Invoice(Base):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(CHAR(36), nullable=False)
    sale_date = Column(DateTime, nullable=False)
    invoice_number = Column(String(255), nullable=False)
    payment_method = Column(String(255), nullable=False)
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
    session = Session()
    invoices = session.query(Invoice).all()
    print(f"Facturas obtenidas: {len(invoices)}")
    session.close()
    return render_template('facturas.html', invoices=invoices)

# Credenciales para conectarse a RabbitMQ
credentials = pika.PlainCredentials('admin', 'admin')

# Conectar al servidor RabbitMQ
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        hostname='component-event',
        port=5672,  # Cambia a 5672 para AMQP
        virtual_host='/',
        credentials=credentials
    ))
    channel = connection.channel()
except Exception as e:
    print(f"Error al conectar a RabbitMQ: {e}")
    exit(1)

channel.queue_declare(queue='saleQueue')

def callback(ch, method, properties, body):
    message = body.decode()
    print(f" [x] Recibido: {message}")

    data = json.loads(message)
    sale_date = datetime.strptime(data['SaleDate'], "%Y-%m-%dT%H:%M:%S.%fZ")

    invoice = Invoice(
        customer_id=data['CustomerId'],
        sale_date=sale_date,
        invoice_number=data['InvoiceNumber'],
        payment_method=data['PaymentMethod'],
        total_sale=data['TotalSale'],
        status=data['Status']
    )

    session = Session()
    session.add(invoice)
    session.commit()
    session.close()
    print(f" [x] Factura guardada en la base de datos: {data}")

    # Acknowledge message
    ch.basic_ack(method.delivery_tag)

# Consumir mensajes de la cola
channel.basic_consume(queue='saleQueue', on_message_callback=callback, auto_ack=False)

def run_consumer():
    print(' [*] Esperando mensajes. Para salir presiona CTRL+C')
    channel.start_consuming()

def signal_handler(sig, frame):
    print('Cerrando...')
    connection.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    consumer_thread = threading.Thread(target=run_consumer)
    consumer_thread.start()

    app.run(host='0.0.0.0', port=4000, debug=True, use_reloader=False)

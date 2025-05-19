import pika
import json
import os

def send_message_to_queue(message_data):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'localhost'))
    )
    channel = connection.channel()
    channel.queue_declare(queue='chat_queue', durable=True)

    channel.basic_publish(
        exchange='',
        routing_key='chat_queue',
        body=json.dumps(message_data),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

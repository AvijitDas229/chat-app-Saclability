import pika
import json
import time
import os

def callback(ch, method, properties, body):
    data = json.loads(body)
    print(f" [x] Received message: {data}")
    # Simulate background processing
    time.sleep(1)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.environ.get('RABBITMQ_HOST', 'localhost'))
    )
    channel = connection.channel()
    channel.queue_declare(queue='chat_queue', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='chat_queue', on_message_callback=callback)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()

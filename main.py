#Main python file for gloocel_pi 
from gpiozero import LED
from time import sleep 
import pika
import pika.exceptions
import os 
from retry import retry
from dotenv import load_dotenv
from pika.adapters.utils import connection_workflow

#Environment Variables
load_dotenv()

RMQ_USER = os.getenv('RMQ_USER')
PASS = os.getenv('PASS')
IP = os.getenv('IP')
PORT = os.getenv('PORT')
CREDENTIALS = pika.PlainCredentials(RMQ_USER, PASS)

#GPIO port 18 assigned to led 
led_red = LED(18)

#GPIO port 17 assigned to led
led_green = LED(17)

#Doors that are assigned to queues
Queue1 = "Eddy's Door"
Queue2 = "Herbert's Door"

#Callback method that takes in an led 
def callback(body, led):
 print(" [x] Received %r" % body)
 message = body.decode("utf-8")
 message = message.lower()
 if ('open' in message):
  led.on()
  sleep(5)
  led.off()
  print("Success, Opened Door")
 elif ('close' in message):
  led.off()
  print("Success, Closed Door")
 else:
  led.off()
  print("other")

@retry(exceptions = (pika.exceptions.AMQPConnectionError, connection_workflow.AMQPConnectorException), tries = -1, delay=5, jitter=(1, 3), backoff=1.05)
def main():
 print("Connecting . . .")
 connection = pika.BlockingConnection(pika.ConnectionParameters(IP, PORT, '/', CREDENTIALS))
 channel = connection.channel()

 """
 Queue attribute needs to be changed when wanting to control a new door/queue
 First Queue/Door, controls RED led
 """
 channel.basic_consume(queue=Queue1, on_message_callback=lambda ch, method, properties, body: callback(body, led_red), auto_ack=True)
 
 """
 Second Queue/Door, controls GREEN led
 """
 channel.basic_consume(queue=Queue2, on_message_callback=lambda ch, method, properties, body: callback(body, led_green), auto_ack=True)
 
 try:
  print(' [*] Waiting for messages. To exit press CTRL+C')
  channel.start_consuming()
 except KeyboardInterrupt:
  channel.stop_consuming()
  connection.close()
 except pika.exceptions.ConnectionClosedByBroker as e:
  print(e)
  print("Restarting connection . . .")
  raise e
 except connection_workflow.AMQPConnectorException as e:
  print(e)
  print("Restarting connection . . .")
  raise e
 

if __name__ == "__main__":
 main()


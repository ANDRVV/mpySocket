# mpySocket
A socket for the esp01 and esp01s.

# Example

```python
import mpySocket, time
from machine import Pin

socket = mpySocket.setup(0, 1)

socket.connectNetwork("SUPERROUTER", "superpassword")
socket.createServer(12000, socket.TCP) 

led1 = Pin(15, Pin.OUT)
led1.value(1)
led = Pin(28, Pin.OUT)
while True:
    time.sleep(0.1)
    try:
        data = socket.recv(100)
        if "on" in data:
            led.value(1)
        elif "off" in data:
            led.value(0)
        elif "quit" in data:
            break
        else:
            pass
    except:
        pass
socket.deleteServer()
socket.disconnectNetwork()
led1.value(0)
led.value(0)

```

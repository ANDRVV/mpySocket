# mpySocket
A socket lib for the esp01 and esp01s.

# Info

## All Protocol

- TCP
- TCPv6 (IPv6)
- SSL
- SSLv6 (IPv6)

## What mpySocket can do

- Verify if ESP01/ESP01s is started or it works;
- Restart ESP01/ESP01s;
- Get local IPv4;
- Get local MAC Address;
- Get WiFi Mode;
- Set WiFi Mode (default is SoftAP+STA (3));
- Scan Networks,
- Connect/Disconnect to Network;
- Create/Delete Server;
- Connect/Disconnect to a server;
- Send/Recv Message (with a specific buffer).


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

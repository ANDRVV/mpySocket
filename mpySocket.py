import machine, time

OK_CODE = "OK\r\n"

class socket():
    TCP = "proto.tcp_4"  
    TCPv6 = "proto.tcp_6"
    SSL = "proto.ssl_4"
    SSLv6 = "proto.ssl_6"
    
    def __init__(self, UARTCode):
        self.UARTCode = UARTCode
        self.connected = False
        self.IPv6Enabled = False
        self.networkConnected = False
        self.serverConnected = False
        self.serverCreated = False
        self.setWiFiMode("3")
        
    def itStarted(self):
        data = _send_ESP01(self.UARTCode, "AT\r\n")
        return OK_CODE in data if data is not None else False
        
    def restart(self):
        data = _send_ESP01(self.UARTCode, "AT+RST\r\n")
        return OK_CODE in data if data is not None else False

    def getLocalIPv4(self):
        response = _send_ESP01(self.UARTCode, "AT+CIFSR\r\n")
        return response.replace("+CIFSR:APIP,", "").replace("\r\n+CIFSR:APMAC,", "").replace("\r\n+CIFSR:STAIP,", "").replace("\r\n+CIFSR:STAMAC,", "").replace("\r\n\r\OK_CODE", "").split('""')[2].strip('"')

    def getLocalMAC(self):
        response = _send_ESP01(self.UARTCode, "AT+CIFSR\r\n")
        return response.replace("+CIFSR:APIP,", "").replace("\r\n+CIFSR:APMAC,", "").replace("\r\n+CIFSR:STAIP,", "").replace("\r\n+CIFSR:STAMAC,", "").replace("\r\n\r\OK_CODE", "").split('""')[3].strip('"')

    def getWiFiMode(self):
        data = _send_ESP01(self.UARTCode, "AT+CWMODE_CUR?\r\n")
        if not data:
            return None
        modes = {"1": "STA", "2": "SoftAP", "3": "SoftAP+STA"}
        return next((modes[m] for m in modes if m in data), None)

    def setWiFiMode(self, mode):
        mode_map = {"STA": 1, "SoftAP": 2, "SoftAP+STA": 3}
        mode_num = mode_map.get(mode, mode)
        data = _send_ESP01(self.UARTCode, f"AT+CWMODE_CUR={mode_num}\r\n")
        return data and OK_CODE in data

    def getOnlineNetworks(self, timeToResearch: int):
        data = _send_ESP01(self.UARTCode, "AT+CWLAP\r\n", delay=timeToResearch)
        if not data:
            return None
        clean_data = (data.replace("+CWLAP:", "")
                        .replace(r"\r\n\r\nOK\r\n", "")
                        .replace(r"\r\n", "@")
                        .replace("b'(", "(")
                        .replace("'", ""))
        return [line.strip("()").split(",") for line in clean_data.split("@")]
    
    def connectNetwork(self, SSID: str, Password: str) -> str:
        if self.networkConnected:
            return "ALREADY CONNECTED TO A NETWORK"
            
        self.networkConnected = True
        data = _send_ESP01(self.UARTCode, "AT+CWJAP_CUR="+'"'+SSID+'"'+','+'"'+Password+'"', delay = 5)
        return "Connected to WiFi" if data else "Unable to connect"
    
    def disconnectNetwork(self) -> bool:
        if not self.networkConnected:
            return "NOT CONNECTED"
        
        data = _send_ESP01(self.UARTCode, "AT+CWQAP")
        if data and OK_CODE in data:
            self.networkConnected = False
            return True
        return False
            
    def createServer(self, port: int, protocol: str) -> str:
        if not self.networkConnected:
            return "NO CONNECTION FROM NETWORK"
        if self.serverCreated:
            return "ALREADY SERVER CREATED"
        if self.serverConnected:
            return "ALREADY CONNECTED TO A SERVER"
        
        port = str(port)
        
        match protocol:
            case socket.TCP:
                _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                response = _send_ESP01(self.UARTCode, "AT+CIPSERVER=1," + port + "\r\n")
            case socket.TCPv6:
                _send_ESP01(self.UARTCode, "AT+CIPV6=1")
                self.IPv6Enabled = True
                _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                response = _send_ESP01(self.UARTCode, "AT+CIPSERVER=1," + port + ',"' + "TCPv6" + '"' + "\r\n")
            case socket.SSL:
                _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                response = _send_ESP01(self.UARTCode, "AT+CIPSERVER=1," + port + ',"' + "SSL" + '",1' + "\r\n")
            case socket.SSLv6:
                self.IPv6Enabled = True
                _send_ESP01(self.UARTCode, "AT+CIPV6=1")
                _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                response = _send_ESP01(self.UARTCode, "AT+CIPSERVER=1," + port + ',"' + "SSLv6" + '",1' + "\r\n")
            case _:
                return "INVALID PROTOCOL"
            
        self.serverCreated = OK_CODE in response  
        return response
    
    def deleteServer(self) -> str:
        if not self.networkConnected:
            return "NO CONNECTION FROM NETWORK"
        if not self.serverCreated:
            return "SERVER NOT CREATED"
        if self.serverConnected:
            return "IMPOSSIBLE DELETE A NOT EXISTENT SERVER"
            
        return _send_ESP01(self.UARTCode, "AT+CIPSERVER=0,1\r\n")
        
    def connect(self, host: str, port: int, protocol: str) -> str:
        if not self.networkConnected:
            return "NO CONNECTION FROM NETWORK"
        if self.serverCreated:
            return "ALREADY SERVER CREATED"
        if self.serverConnected:
            return "ALREADY CONNECTED TO A SERVER"
        
        port = str(port)
        
        match protocol:
            case socket.TCP:
                _send_ESP01(self.UARTCode, "AT+CIPMODE=0")
                _send_ESP01(self.UARTCode, "AT+CIPMUX=1")
                response = _send_ESP01(self.UARTCode, "AT+CIPSTART="+'"'+"TCP"+'"'+","+'"' + host + '"' + ',' + port)
            case socket.TCPv6:
                self.IPv6Enabled = True
                _send_ESP01(self.UARTCode, "AT+CIPV6=1")
                _send_ESP01(self.UARTCode, "AT+CIPMODE=0")
                _send_ESP01(self.UARTCode, "AT+CIPMUX=1")
                response = _send_ESP01(self.UARTCode, "AT+CIPSTART="+'"'+"TCPv6"+'"'+","+'"' + host + '"' + ',' + port)
            case socket.SSL:
                _send_ESP01(self.UARTCode, "AT+CIPMODE=0")
                _send_ESP01(self.UARTCode, "AT+CIPMUX=1")
                response = _send_ESP01(self.UARTCode, "AT+CIPSTART="+'"'+"SSL"+'"'+","+'"' + host + '"' + ',' + port)
            case socket.SSLv6:
                self.IPv6Enabled = True
                _send_ESP01(self.UARTCode, "AT+CIPV6=1")
                _send_ESP01(self.UARTCode, "AT+CIPMODE=0")
                _send_ESP01(self.UARTCode, "AT+CIPMUX=1")
                response = _send_ESP01(self.UARTCode, "AT+CIPSTART="+'"'+"SSLv6"+'"'+","+'"' + host + '"' + ',' + port)
            case _:
                return "INVALID PROTOCOL"
            
        self.serverConnected = OK_CODE in response  
        return response
        
        
    def disconnect(self) -> str:
        if not self.networkConnected:
            return "NO CONNECTION FROM NETWORK"
        if not self.serverConnected:
            return "IMPOSSIBLE DISCONNECT A NOT EXISTENT CLIENT"
        
        return _send_ESP01(self.UARTCode, "AT+CIPCLOSE")
            
        
    def send(self, msg: str) -> str:
        if not self.networkConnected:
            return "NO CONNECTION FROM NETWORK"
        if not self.serverConnected and not self.serverCreated:
            return "NO CONNECTION ESTABLISHED"

        r1 = _send_ESP01(self.UARTCode, "AT+CIPSENDL=0," + len(msg))
        r2 = _send_ESP01(self.UARTCode, msg)
        return r1 + r2
            
    def recv(self, buffer: int) -> str:
        if not self.networkConnected:
            return "NO CONNECTION FROM NETWORK"
        if not self.serverConnected and not self.serverCreated:
            return "NO CONNECTION ESTABLISHED"

        return _send_ESP01(self.UARTCode, "AT+CIPRECVDATA=0," + str(buffer)).replace("+IPD,0,2:", "")
        
def setup(
    txPin: int,
    rxPin: int,
    uartPort: int = 0,
    baudrate: int = 115200
) -> socket:
    uartCode = machine.UART(
        uartPort,
        baudrate = baudrate,
        tx = machine.Pin(txPin),
        rx = machine.Pin(rxPin),
        txbuf = 1024,
        rxbuf = 1024*2
    )
    
    _send_ESP01(uartCode, "ATE0")
    _send_ESP01(uartCode, "AT+RESTORE")
    
    return socket(uartCode)

def _send_ESP01(uartCode, cmd: str, delay: float = 1.0) -> str:
    if not cmd.endswith("\r\n"):
        cmd += "\r\n"
    
    uartCode.write(cmd)
    time.sleep(delay)
    
    while not uartCode.any():
        time.sleep(0.1)
        
    comment: bytes
    while uartCode.any():
        comment += uartCode.read(2048)

    try:
        return cmd.decode()
    except:
        return str(comment)

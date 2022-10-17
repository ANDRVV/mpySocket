from machine import Pin, UART
import time

comment, msg = None, None
OK_CODE = "OK\r\n"
ERROR_CODE = "ERROR\r\n"
FAIL_CODE = "FAIL\r\n"
WIFI_CONNECTED_CODE = "WIFI CONNECTED\r\n"
WIFI_GOT_IP_CONNECTED_CODE = "WIFI GOT IP\r\n"
WIFI_DISCONNECTED_CODE = "WIFI DISCONNECT\r\n"
WIFI_AP_NOT_PRESENT_CODE = "WIFI AP NOT FOUND\r\n"
WIFI_AP_WRONG_PWD_CODE = "WIFI AP WRONG PASSWORD\r\n"
BUSY_CODE = "busy p...\r\n"

def setup(txPin, rxPin, uartPort = 0, baudRate = 115200):   
    UARTCode = UART(uartPort, baudrate = baudRate, tx = Pin(txPin), rx = Pin(rxPin), txbuf = 1024, rxbuf = 1024*2)
    _send_ESP01(UARTCode, "ATE0\r\n")
    _send_ESP01(UARTCode, "AT+RESTORE\r\n")
    return socket(UARTCode)

def _send_ESP01(UARTCode, msg, delay = 1):
    comment = str()
    UARTCode.write(msg)
    comment = bytes()
    time.sleep(delay)
    while True:
        if UARTCode.any() > 0:
            break
    while UARTCode.any() > 0:
        comment += UARTCode.read(1024*2)
    try:
        comment = comment.decode()
    except:
        pass
    return comment

class socket:
    TCP = "proto.tcp_4"  
    TCPv6 = "proto.tcp_6"
    SSL = "proto.ssl_4"
    SSLv6 = "proto.ssl_6"

    def __init__(self, UARTCode):
        self.UARTCode = UARTCode
        self.IPv6Enabled = False
        self.networkConnected = False
        self.serverConnected = False
        self.serverCreated = False
        self.setWiFiMode("3")
 
    def itStarted(self):
        data = _send_ESP01(self.UARTCode, "AT\r\n")
        if data != None:
            if OK_CODE in data:
                return True
            else:
                return False
        else:
            return False
        
    def restart(self):
        data = _send_ESP01(self.UARTCode, "AT+RST\r\n")
        if data != None:
            if OK_CODE in data:
                return True
            else:
                return False
        else:
            return False

    def getLocalIPv4(self):
        netargs1 = _send_ESP01(self.UARTCode, "AT+CIFSR\r\n").replace("+CIFSR:APIP,", "").replace("\r\n+CIFSR:APMAC,", "").replace("\r\n+CIFSR:STAIP,", "").replace("\r\n+CIFSR:STAMAC,", "").replace("\r\n\r\OK_CODE", "")
        netargs1 = netargs1.split('""')
        netargs = []
        for arg in netargs1:
            netargs.append(arg.replace('"', ""))
        return netargs[2]
    
    def getLocalMAC(self):
        netargs1 = _send_ESP01(self.UARTCode, "AT+CIFSR\r\n").replace("+CIFSR:APIP,", "").replace("\r\n+CIFSR:APMAC,", "").replace("\r\n+CIFSR:STAIP,", "").replace("\r\n+CIFSR:STAMAC,", "").replace("\r\n\r\OK_CODE", "")
        netargs1 = netargs1.split('""')
        netargs = []
        for arg in netargs1:
            netargs.append(arg.replace('"', ""))
        return netargs[3]
    
    def getWiFiMode(self):
        data = _send_ESP01(self.UARTCode, "AT+CWMODE_CUR?\r\n")
        if data != None:
            if "1" in data:
                return "STA"
            elif "2" in data:
                return "SoftAP"
            elif "3" in data:
                return "SoftAP+STA"
            else:
                return None
        else:
            return None
    
    def setWiFiMode(self, mode: str):
        try:
            int(mode)
            data = _send_ESP01(self.UARTCode, "AT+CWMODE_CUR="+str(mode)+"\r\n")
        except:
            if mode == "STA":
                mode = 1
            elif mode == "SoftAP":
                mode = 2
            elif mode == "SoftAP+STA":
                mode = 3
            data = _send_ESP01(self.UARTCode, "AT+CWMODE_CUR="+str(mode)+"\r\n")
        if data != None:
            if OK_CODE in data:   
                return True
            else:
                return False
        else:
            return False
    
    def getOnlineNetworks(self, timeToResearch: int):
        data = _send_ESP01(self.UARTCode, "AT+CWLAP\r\n", delay = timeToResearch)
        if data != None:
            data = data.replace("+CWLAP:", "")
            data = data.replace(r"\r\n\r\nOK\r\n", "")
            data = data.replace(r"\r\n","@")
            data = data.replace("b'(","(").replace("'","")
            data = data.split("@")
            data = list(data)
            apList = list()
            for items in data:
                data = str(items).replace("(","").replace(")","").split(",")
                data = list(data)
                apList.append(data)
            return apList
        else:
            return None
    
    def connectNetwork(self, SSID: str, Password: str):
        if self.networkConnected != True:
            self.networkConnected = True
            data = _send_ESP01(self.UARTCode, "AT+CWJAP_CUR="+'"'+SSID+'"'+','+'"'+Password+'"'+"\r\n", delay = 5)
            if data != None:
                return WIFI_CONNECTED_CODE
            else:
                return WIFI_DISCONNECTED_CODE
        else:
            return "ALREADY CONNECTED TO A NETWORK"
    
    def disconnectNetwork(self):
        if self.networkConnected == True:
            data = _send_ESP01(self.UARTCode, "AT+CWQAP\r\n")
            if data != None:
                if OK_CODE in data:
                    self.networkConnected = False
                    return True
                else:
                    return False
            else:
                return False
        else:
            return "NOT CONNECTED"
            
    def createServer(self, port: int, protocol: str):
        port = str(port)
        if self.networkConnected:
            if self.serverCreated == False:
                if self.serverConnected == False:
                    if protocol == socket.TCP:
                        _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                        _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                        response = _send_ESP01(self.UARTCode, "AT+CIPSERVER=1," + port + "\r\n")
                        if OK_CODE in response:
                            self.serverCreated = True
                        return response
                    elif protocol == socket.TCPv6:
                        _send_ESP01(self.UARTCode, "AT+CIPV6=1")
                        self.IPv6Enabled = True
                        _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                        _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                        response = _send_ESP01(self.UARTCode, "AT+CIPSERVER=1," + port + ',"' + "TCPv6" + '"' + "\r\n")
                        if OK_CODE in response:
                            self.serverCreated = True
                        return response
                    elif protocol == socket.SSL:
                        _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                        _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                        response = _send_ESP01(self.UARTCode, "AT+CIPSERVER=1," + port + ',"' + "SSL" + '",1' + "\r\n")
                        if OK_CODE in response:
                            self.serverCreated = True
                        return response
                    elif protocol == socket.SSLv6:
                        self.IPv6Enabled = True
                        _send_ESP01(self.UARTCode, "AT+CIPV6=1")
                        _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                        _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                        response = _send_ESP01(self.UARTCode, "AT+CIPSERVER=1," + port + ',"' + "SSLv6" + '",1' + "\r\n")
                        if OK_CODE in response:
                            self.serverCreated = True
                        return response
                    else:
                        return "INVALID PROTOCOL"
                else:
                    return "ALREADY CONNECTED TO A SERVER"
            else:
                return "ALREADY SERVER CREATED"
        else:
            return "NO CONNECTION FROM NETWORK"
    
    def deleteServer(self):
        if self.networkConnected:
            if self.serverCreated == True:
                if self.serverConnected == False:
                    response = _send_ESP01(self.UARTCode, "AT+CIPSERVER=0,1\r\n")
                    return response
                else:
                    return "IMPOSSIBLE DELETE A NOT EXISTENT SERVER"
            else:
                return "SERVER NOT CREATED"
        else:
            return "NO CONNECTION FROM NETWORK"
        
    def connect(self, host: str, port: int, protocol: str):
        port = str(port)
        if self.networkConnected:
            if self.serverCreated == False:
                if self.serverConnected == False:
                    if protocol == socket.TCP:
                        _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                        _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                        response = _send_ESP01(self.UARTCode, "AT+CIPSTART="+'"'+"TCP"+'"'+","+'"' + host + '"' + ',' + port + "\r\n")
                        if OK_CODE in response:
                            self.serverConnected = True
                        return response
                    elif protocol == socket.TCPv6:
                        _send_ESP01(self.UARTCode, "AT+CIPV6=1")
                        self.IPv6Enabled = True
                        _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                        _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                        response = _send_ESP01(self.UARTCode, "AT+CIPSTART="+'"'+"TCPv6"+'"'+","+'"' + host + '"' + ',' + port + "\r\n")
                        if OK_CODE in response:
                            self.serverConnected = True
                        return response
                    elif protocol == socket.SSL:
                        _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                        _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                        response = _send_ESP01(self.UARTCode, "AT+CIPSTART="+'"'+"SSL"+'"'+","+'"' + host + '"' + ',' + port + "\r\n")
                        if OK_CODE in response:
                            self.serverConnected = True
                        return response
                    elif protocol == socket.SSLv6:
                        self.IPv6Enabled = True
                        _send_ESP01(self.UARTCode, "AT+CIPV6=1")
                        _send_ESP01(self.UARTCode, "AT+CIPMODE=0\r\n")
                        _send_ESP01(self.UARTCode, "AT+CIPMUX=1\r\n")
                        response = _send_ESP01(self.UARTCode, "AT+CIPSTART="+'"'+"SSLv6"+'"'+","+'"' + host + '"' + ',' + port + "\r\n")
                        if OK_CODE in response:
                            self.serverConnected = True
                        return response
                    else:
                        return "INVALID PROTOCOL"
                else:
                    return "ALREADY CONNECTED TO A SERVER"
            else:
                return "ALREADY SERVER CREATED"
        else:
            return "NO CONNECTION FROM NETWORK"
        
    def disconnect(self):
        if self.networkConnected:
            if self.serverConnected == True: 
                    response = _send_ESP01(self.UARTCode, "AT+CIPCLOSE\r\n")
                    return response
            else:
                return "IMPOSSIBLE DISCONNECT A NOT EXISTENT CLIENT"  
        else:
            return "NO CONNECTION FROM NETWORK" 
        
    def send(self, msg: str):
        if len(msg.encode()) >= 8192:
            if self.networkConnected:
                if self.serverConnected == True or self.serverCreated == True: 
                        response1 = _send_ESP01(self.UARTCode, "AT+CIPSENDL=0," + len(msg.encode()) + "\r\n")
                        response2 = _send_ESP01(self.UARTCode, msg + "\r\n")
                        return response1 + response2
                else:
                    return "NO CONNECTION ESTABLISHED"  
            else:
                return "NO CONNECTION FROM NETWORK" 
        else:
            if self.networkConnected:
                if self.serverConnected == True or self.serverCreated == True: 
                        response1 = _send_ESP01(self.UARTCode, "AT+CIPSENDL=0," + len(msg.encode()) + "\r\n")
                        response2 = _send_ESP01(self.UARTCode, msg + "\r\n")
                        return response1 + response2
                else:
                    return "NO CONNECTION ESTABLISHED"  
            else:
                return "NO CONNECTION FROM NETWORK" 
            
    def recv(self, buffer: int):
        buffer = str(buffer)
        if self.networkConnected:
            if self.serverConnected == True or self.serverCreated == True: 
                    response = _send_ESP01(self.UARTCode, "AT+CIPRECVDATA=0," + buffer + "\r\n").replace("+IPD,0,2:", "")
                    return response
            else:
                return "NO CONNECTION ESTABLISHED"  
        else:
            return "NO CONNECTION FROM NETWORK"

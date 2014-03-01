import socket
import select
import threading
import sys
import SocketServer
import struct
import time
import sys

class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
class Socks(SocketServer.StreamRequestHandler):
    iplist = ['127.0.0.1', '192.168.1.186']
    def send_all(self, socket, data):
        bytes_sent = 0
        while True:
            r = socket.send(data[bytes_sent:])
            if r <0:
                return r
            bytes_sent += r
            if bytes_sent == len(data):
                return bytes_sent
    def handle_tcp(self, sock, remote):
        try:
            fdset = [sock, remote]
            while True:
                r, w, e = select.select(fdset, [], [])
                if sock in r:
                    data = sock.recv(4096)
                    if len(data) <= 0:
                        break
                    results = self.send_all(remote, data)
                
                if remote in r:
                    data = remote.recv(4096)
                    if len(data) <= 0:
                        break
                    results = self.send_all(sock, data)
        finally:
            remote.close()
            sock.close()


    def handle(self):
        try:
            print 'socks connection from ', self.client_address, self.__class__.iplist
            sock = self.connection
            data = sock.recv(262) 
                                
            if self.client_address[0] in self.__class__.iplist:
                reply = b"\x05\x00"   # no auth and ok
            else:
                reply = b"\x05\xff"
            sock.send(reply);
            data = self.rfile.read(4)
            mode = ord(data[1])
            addrtype = ord(data[3])
            if addrtype == 1:
                addr = socket.inet_ntoa(self.rfile.read(4))
            elif addrtype == 3:
                addr = self.rfile.read(ord(sock.recv(1)[0]))
            
            port = struct.unpack('>H', self.rfile.read(2))
            reply = b"\x05\x00\x00\x01"
            try:
                if mode == 1:
                    remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote.connect((addr, port[0]))
                    print 'Tcp connect to', addr, port[0]
                else:
                    reply = b"\x05\x07\x00\x01"
                local = remote.getsockname()
                print local
                reply += socket.inet_aton(local[0])+struct.pack('>H', local[1])
                sys.stdout.flush()
                           
            except socket.error:
                reply = '\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00'

            
            print ord(reply[1])
            sock.send(reply)
            if reply[1] == '\x00':
                if mode == 1:
                    self.handle_tcp(sock, remote)
        except socket.error:
            print 'socket error'

def main():
    server = ThreadingTCPServer(('', 1080), Socks)
    threading.Thread(target=server.serve_forever).start()

if __name__=='__main__':
    main()


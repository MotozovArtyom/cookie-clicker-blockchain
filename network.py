from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

import nmap.nmap as nmap

import json
import os
import hashlib
from time import time
import netifaces


def generate_nodeid():
    return hashlib.sha256(os.urandom(256 // 8)).hexdigest()[:10]


class MyProtocol(Protocol):
    def __init__(self, factory, peertype):
        self.factory = factory
        self.state = "HELLO"
        self.remote_nodeid = None
        self.nodeid = self.factory.nodeid
        self.peertype = peertype
        self.lastping = None

    def connectionMade(self):
        remote_ip = self.transport.getPeer()
        host_ip = self.transport.getHost()
        self.remote_ip = remote_ip.host + ":" + str(remote_ip.port)
        self.host_ip = host_ip.host + ":" + str(host_ip.port)
        print("Connection from", self.transport.getPeer())

    def connectionLost(self, reason=None):
        if self.remote_nodeid in self.factory.peers:
            self.factory.peers.pop(self.remote_nodeid)
            self.lc_ping.stop()
        print(self.nodeid, "disconnected")

    def dataReceived(self, data):
        """
        :param data: нужно создать какой-то спец сигнал,
        который входит в data, чтобы определить, как действовать дальше
        *кто-то новый пришел и отправить весь blockchain
        *создан новый block и его нужно отправить
        *создан новый block и остальных нужно остановить на некоторое время
        :return:
        """
        print(data)
        print(type(data))
        self.transport.write(b"HAI")

    def send_addr(self, mine=False):
        now = time()
        if mine:
            peers = [self.host_ip]
        else:
            peers = [(peer.remote_ip, peer.remote_nodeid)
                     for peer in self.factory.peers
                     if peer.peertype == 1 and peer.lastping > now - 240]
        addr = json.puts({'msgtype': 'addr', 'peers': peers})
        self.transport.write(peers + "\n")

    def send_hello(self):
        hello = json.puts({'nodeid': self.nodeid, 'msgtype': 'hello'})
        self.transport.write(hello + "\n")

    def send_block(self, block):
        """send_block
        block - это data, которую нам придет от GUIшки (блок по сути),
        а отправлять мы его будем через socket сюда, а потом рассылать другим пирам"""
        block = json.puts(block)
        self.transport.write(block)


class MyFactory(Factory):
    def __init__(self):
        pass

    def startFactory(self):
        self.peers = {}
        self.nodeid = generate_nodeid()

    def buildProtocol(self, addr):
        return MyProtocol(self, 1)


def gotProtocol(p):
    p.send_hello()


def discover_hosts(mask):
    port_scanner = nmap.PortScanner()
    port_scanner.scan(hosts='192.168.1.0/24', arguments='-n -sP')
    return [(x, port_scanner[x]['status']['state']) for x in port_scanner.all_hosts()]


def main():
    interfaces = netifaces.interfaces()
    try:
        addr = netifaces.ifaddresses(interfaces[2])
        host_addr = addr[netifaces.AF_INET][0]["addr"]
    except:
        addr = netifaces.ifaddresses(interfaces[1])
        host_addr = addr[netifaces.AF_INET][0]["addr"]
    port = 5500
    endpoint = TCP4ServerEndpoint(reactor, port)
    factory = MyFactory()
    endpoint.listen(factory)
    hosts_list = discover_hosts(None)
    for host, status in hosts_list:
        if host != host_addr:
            point = TCP4ClientEndpoint(reactor, host, int(port))
            point.connect(factory)
    reactor.run()


if __name__ == '__main__':
    main()
    # p = Process(target=main)
    # p.start()
    # print("It's ME")
    # p.join()
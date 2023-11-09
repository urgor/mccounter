"""
# McCounter tool
McCounter is tool to track amount of MC users (players) and monitor server's heartbeat. Returns two gauge Prometeus metrics.
Could be used as is (see help below) or assembled into Docker container (see dockerfile)

## Usage
python3 mccounter.py <MC_ip> <mcpi_e-port> <mccounter_port>

## Dependencies
* mcpi_e -- for python API to Minecraft
* * mcpi_e uses RaspberryJuice Minecraft plugin
* prometheus_client -- to format Prometheus metrics and raise simple server for it.

## Docker
docker build -t McCounter .
docker run -p 9101:9101 --rm McCounter <my-mc-host> <mcpi_e-port-4711> <port-for-this-server-9101>

## Author
Urgor, urgorka@gmail.com
"""

import sys
import select
import time

from mcpi_e.connection import Connection, RequestError
from prometheus_client import start_http_server, Gauge


class DrainError(Exception):
    pass


class MaConnection(Connection):
    """
    Extends from Connection because it handles socker connection not very well. In case when server is down that method
    shits tons of shit to stderr, and do nothing to inform upper layer about problem nor undertakes attempt to re-connect.
    """
    def drain(self):
        """Drains the socket of incoming data"""
        while True:
            readable, _, _ = select.select([self.socket], [], [], 0.0)
            # when ok
            # []
            # when not ok
            # [<socket.socket fd=4, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0, laddr=('192.168.2.13', 36934), raddr=('192.168.2.35', 4711)>]

            if not readable:
                return

            self.socket.close()
            raise DrainError()


class Twitcher:
    """
    Connect to MC server through mcpi_e, get (1) count of users metric, handle errors to return (2) heartbeat metric.
    """
    def __init__(self, ip, port):
        self.con = None
        self.ip = ip
        self.port = port
        self.connect()

    def connect(self):
        """ Connect or reconnect to server """
        if self.con is not None:
            return
        try:
            self.con = MaConnection(self.ip, self.port)
            print(f'Connected to {self.ip}:{self.port} successfully')
        except ConnectionRefusedError as e:
            self.con = None
            print(f'Error {e.__class__} {e.errno} {e.strerror}')

    def count_users(self):
        """ Count users metric """
        if self.con is None:
            return 0
        try:
            ids = self.con.sendReceive(b"world.getPlayerIds")
            info = list(map(int, ids.split("|")))
            return len(info)
        except RequestError:
            # can't execute "world.getPlayerIds" command -- there is no players
            return 0
        except DrainError:
            # there is no more server in the other side
            print('MC server have gone away')
            self.con = None
            return 0

    def heartbeat(self):
        """ Heartbeat metric """
        return self.con is not None


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('McCounter is tool to track amount of MC users and servers heartbeat in two gauge Prometeus metrics.')
        print('Usage: python3 mccounter.py <MC_ip> <MC_port> <mccounter_port>')
        sys.exit(1)
    print(f'Starting Prometeus client-server at {sys.argv[3]}, connect to MC {sys.argv[1]}:{sys.argv[2]}')

    twitcher = Twitcher(str(sys.argv[1]), int(sys.argv[2]))

    counter = Gauge('mcCountUsers', 'Current active players on MC server')
    counter.set_function(twitcher.count_users)
    heartbeat = Gauge('mcHeartbeat', 'Heartbeat of MC server')
    heartbeat.set_function(twitcher.heartbeat)

    # Start up the server to expose the metrics.
    start_http_server(int(sys.argv[3]))

    while True:
        time.sleep(5)
        twitcher.connect()

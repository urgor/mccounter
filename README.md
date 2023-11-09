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

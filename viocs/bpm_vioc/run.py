from .ioc import get_pv_database, SimpleServer, MyDriver

pv_database = get_pv_database()

server = SimpleServer()
server.createPV(prefix, pv_database)

driver = MyDriver(pv_database)

while True:
    server.process(0.1)

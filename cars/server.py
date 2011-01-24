import time
import datetime
import logging
from threading import Thread
from twisted.internet import defer
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import reactor

class TrafficServer(object):
  """
  Server main class
  """
  def __init__(self):
    """
    Constructor
    """
    # init logging facility: log to client.log
    logging.basicConfig(filename='server.log', level=logging.DEBUG, filemode='w+')
    logging.debug('Traffic server init')
    # cars list
    self.cars = []
    # server listening interface
    self.interface = 'localhost'
    # server port number
    self.port = 8000
    # Factory class for connections
    self.factory = TrafficFactory(self.cars)
    # Thread monitoring for new cars
    self.watchcars = WatchCars(self.cars)
    self.watchcars.start()
 
  def listen(self):
    """
    Call reactor's listen to listen for client's connections
    """
    logging.debug('Traffic server listen')
    port = reactor.listenTCP(self.port or 0, self.factory, interface=self.interface)

class TrafficProtocol(Protocol):
  """
  Protocol class to handle data between the client and the server.
  """

  def connectionMade(self):
    """
    Callback when a connection is made. Write cars data to the client then
    claose the connection.
    """
    logging.debug('Connection made')
    data = '.'.join(self.factory.cars)
    self.transport.write(data)
    self.transport.loseConnection()

class TrafficFactory(ServerFactory):
  """
  Factory to create TrafficProtocol instances
  """
    
  protocol = TrafficProtocol

  def __init__(self, cars):
    """
    Constructor.

    @param cars cars list
    """
    logging.debug('Traffic factory init')
    self.cars = cars

class WatchCars(Thread):
  """
  Thread monitoring the cars.
  """

  def __init__(self, cars):
    """
    Constructor.

    @param cars cars list
    """
    logging.debug('Watch cars thread init')
    Thread.__init__(self)
    self.cars = cars
  
  def run(self):
    """
    Thread run. Get new cars and add them to the cars list.
    """
    logging.debug('Watch cars thread run')
    while True:
      #time, brand, color = get_next_car()
      t, brand, color = 'today', 'peugeot', 'red'
      self.cars.append('%s:%s:%s' % (t, brand, color))
      time.sleep(60)


def main():
  server = TrafficServer()
  server.listen()

  reactor.run()

if __name__ == '__main__':
  main()
 

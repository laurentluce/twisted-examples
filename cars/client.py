import time
import datetime
import logging
import sys
import traceback

from twisted.internet import reactor
from twisted.internet import defer
from twisted.internet.protocol import Protocol, ClientFactory

class TrafficClient(object):
  """
  Client
  """
  def __init__(self):
    """
    Constructor
    """
    # init logging facility: log to client.log
    logging.basicConfig(filename='client.log', level=logging.DEBUG, filemode='w+')
    logging.debug('Traffic client init')
    # init deferred object to handle callbacks and failures
    self.deferred = defer.Deferred()
    # init factory to create TrafficProtocol protocol instances
    self.factory = TrafficClientFactory(self.deferred)
    # list of cars
    self.cars = []
    # keep track of servers replying so we know when the overall work
    # is finished
    self.addr_count = 0
    # list of servers to get cars list from
    self.addresses = [('localhost', 8000), ('localhost', 8000)]
 
  def get_cars(self, host, port):
    """
    Connect to server to retrieve list of cars

    @param host server's hostname
    @param port server's port
    """
    logging.debug('Get cars: %s - %d' % (host, port))
    reactor.connectTCP(host, port, self.factory)

  def got_cars(self, cars):
    """
    Callback when cars retrieval is successful

    @param cars data returned by server
    """
    logging.debug('Got cars: %s' % cars)
    self.cars.extend(cars)

  def get_cars_failed(self, err):
    """
    Callback when retrieval from server failed. Log error.

    @param err server error
    """
    logging.debug('Get cars failed: %s' % err)

  def cars_done(self, cars):
    """
    Callback when retrieval operation is finished for all servers.
    Log cars list and stop Twisted reactor loop which is listening to events
    """
    self.addr_count += 1
    if self.addr_count == len(self.addresses):
      logging.debug('Cars done: %s' % self.cars)
      reactor.stop()

  def update_cars(self):
    """
    Retrieve list of cars from all servers. Set callbacks to handle
    success and failure.
    """
    logging.debug('Update cars')
    for address in self.addresses:
      host, port = address
      self.get_cars(host, port)
      self.deferred.addCallbacks(self.got_cars, self.get_cars_failed)
      self.deferred.addBoth(self.cars_done)

class TrafficProtocol(Protocol):
  """
  Protocol class to handle data between the client and the server.
  """

  data = ''

  def dataReceived(self, data):
    """
    Callback when some data is received from server.

    @param data data received from server
    """
    logging.debug('Data received: %s' % data)
    self.data += data

  def connectionLost(self, reason):
    """
    Callback when connection is lost with server. At that point, the
    cars have been receieved.

    @param reason failure object
    """
    logging.debug('Connection lost: %s' % reason)
    self.cars = []
    for c in self.data.split('.'):
      self.cars.append(c)
    self.carsReceived(self.cars)

  def carsReceived(self, cars):
    """
    Called when the cars data are received.

    @param cars data received from the server
    """
    logging.debug('Cars received: %s' % cars)
    self.factory.get_cars_finished(cars)


class TrafficClientFactory(ClientFactory):
  """
  Factory to create TrafficProtocol protocol instances
  """

  protocol = TrafficProtocol

  def __init__(self, deferred):
    """
    Constructor.

    @param deferred callbacks to handle completion and failures
    """
    logging.debug('Traffic client factory init: %s', deferred)
    self.deferred = deferred

  def get_cars_finished(self, cars):
    """
    Callback when the cars data is retrieved from the server successfully

    @param cars data received from the server
    """
    logging.debug('Get cars finished: %s', cars)
    if self.deferred:
      d, self.deferred = self.deferred, None
      d.callback(cars)

  def clientConnectionFailed(self, connector, reason):
    """
    Callback when connection fails

    @param connector connection object.
    @param reason failure object
    """
    logging.debug('Client connection failed: %s - %s' % (connector, reason))
    if self.deferred:
      d, self.deferred = self.deferred, None
      d.errback(reason)

def main():
  client = TrafficClient()
  client.update_cars()
  reactor.run()

if __name__ == '__main__':
  main()


import math
import numpy
import heapq

# a data container for all pertinent information related to fares. (Should we
# add an underway flag and require taxis to acknowledge collection to the dispatcher?)
class FareEntry:

      def __init__(self, origin, dest, time, price=0, taxiIndex=-1):

          self.origin = origin
          self.destination = dest
          self.calltime = time
          self.price = price
          # the taxi allocated to service this fare. -1 if none has been allocated
          self.taxi = taxiIndex
          # a list of indices of taxis that have bid on the fare.
          self.bidders = []

'''
A Dispatcher is a static agent whose job is to allocate fares amongst available taxis. Like the taxis, all
the relevant functionality happens in ClockTick. The Dispatcher has a list of taxis, a map of the service area,
and a dictionary of active fares (ones which have called for a ride) that it can use to manage the allocations.
Taxis bid after receiving the price, which should be decided by the Dispatcher, and once a 'satisfactory' number
of bids are in, the dispatcher should run allocateFare in its world (parent) to inform the winning bidder that they
now have the fare.
'''
class Dispatcher:

      # constructor only needs to know the world it lives in, although you can also populate its knowledge base
      # with taxi and map information.
      def __init__(self, parent, taxis=None, serviceMap=None):

          self._parent = parent
          # our incoming account
          self._revenue = 0
          # the list of taxis
          self._taxis = taxis
          if self._taxis is None:
             self._taxis = []
          # fareBoard will be a nested dictionary indexed by origin, then destination, then call time.
          # Its values are FareEntries. The nesting structure provides for reasonably fast lookup; it's
          # more or less a multi-level hash.
          self._fareBoard = {}
          # serviceMap gives the dispatcher its service area
          self._map = serviceMap
          # Allocation history supports a mild fairness adjustment: taxis that have
          # received fewer jobs get a small advantage when approach times are close.
          self._allocationCount = {}
          # Give taxis a short opportunity to bid, but avoid the starter's fixed
          # five-tick delay when all useful bids are already available.
          self._minimumBidWait = 2
          self._maximumBidWait = 4

      #_________________________________________________________________________________________________________
      # methods to add objects to the Dispatcher's knowledge base
      
      # make a new taxi known.
      def addTaxi(self, taxi):
          if taxi not in self._taxis:
             self._taxis.append(taxi)

      # added 26 August 2026
      # remove an existing taxi
      # FIXME deal with cases where the taxi has allocations
      def removeTaxi(self, taxi):
          try:
              del self._taxis[self._taxis.index(taxi)]
          except ValueError:
              pass

      # incrementally add to the map. This can be useful if, e.g. the world itself has a set of
      # nodes incrementally added. It can then call this function on the dispatcher to add to
      # its map
      def addMapNode(self, coords, neighbours):
          if self._parent is None:
             return AttributeError("This Dispatcher does not exist in any world")
          node = self._parent.getNode(coords[0],coords[1])
          if node is None:
             return KeyError("No such node: {0} in this Dispatcher's service area".format(coords))
          # build up the neighbour dictionary incrementally so we can check for invalid nodes.
          neighbourDict = {}
          for neighbour in neighbours:
              neighbourCoords = (neighbour[1], neighbour[2])
              neighbourNode = self._parent.getNode(neighbour[1],neighbour[2])
              if neighbourNode is None:
                 return KeyError("Node {0} expects neighbour {1} which is not in this Dispatcher's service area".format(coords, neighbour))
              neighbourDict[neighbourCoords] = (neighbour[0],self._parent.distance2Node(node, neighbourNode))
          self._map[coords] = neighbourDict

      # importMap gets the service area map, and can be brought in incrementally as well as
      # in one wodge.
      def importMap(self, newMap):
          # a fresh map can just be inserted
          if self._map is None:
             self._map = newMap
          # but importing a new map where one exists implies adding to the
          # existing one. (Check that this puts in the right values!)
          else:
             for node in newMap.items():
                 neighbours = [(neighbour[1][0],neighbour[0][0],neighbour[0][1]) for neighbour in node[1].items()]
                 self.addMapNode(node[0],neighbours)

      # handover pushes the Dispatcher's known information to a new one coming on. It dumps the complete fare board to the
      # new dispatcher.
      def handover(self, newDispatcher):
          world = self._parent # sending the world makes sure we are operating in the same environment
          # DEBUGME we hope this is the right way of expanding a comprehension to unroll a dictionary
          compressedFareBoard = ((o[0], d[0], t[0], t[1]) for t in k for k in d[1].items() for d in j for j in o[1].items() for o in i for i in self.fareboard.items())
          for f in compressedFareBoard:
              if not newDispatcher.receiveHandover(self._parent, f[0], f[1], f[2], f[3].taxi, f[3].price):
                 return False # handover failed if the new Dispatcher didn't know the parent world
          return True 

      # any legacy fares or taxis from a previous dispatcher can be imported here - future functionality,
      # for the most part
      # FIXME integrate with handover above
      def receiveHandover(self, parent, origin, destination, time, taxi=None, price=0):
          if self._parent == parent:
             # handover implies taxis definitely known to a previous dispatcher. The current
             # dispatcher should thus be made aware of them
             if taxi not in self._taxis:
                self._taxis.append(taxi)
             # add any fares found along with their allocations
             self.newFare(parent, origin, destination, time)
             self._fareBoard[origin][destination][time].taxi = self._taxis.index(taxi)
             self._fareBoard[origin][destination][time].price = price
             return True # successful handover
          return False # unknown networld. Fail.

      #--------------------------------------------------------------------------------------------------------------
      # runtime methods used to inform the Dispatcher of real-time events


      # fares will call this when they appear to signal a request for service.
      def newFare(self, parent, origin, destination, time):
          # only add new fares coming from the same world
          if parent == self._parent:
             fare = FareEntry(origin,destination,time)
             if origin in self._fareBoard:               
                if destination not in self._fareBoard[origin]:
                   self._fareBoard[origin][destination] = {}
             else:
                self._fareBoard[origin] = {destination: {}}
             # overwrites any existing fare with the same (origin, destination, calltime) triplet, but
             # this would be equivalent to saying it was the same fare, at least in this world where
             # a given Node only has one fare at a time.
             self._fareBoard[origin][destination][time] = fare
             
      # abandoning fares will call this to cancel their request
      def cancelFare(self, parent, origin, destination, calltime):
          # if the fare exists in our world,
          if parent == self._parent and origin in self._fareBoard:
             if destination in self._fareBoard[origin]:
                if calltime in self._fareBoard[origin][destination]:
                   # get rid of it
                   print("Fare ({0},{1}) cancelled".format(origin[0],origin[1]))
                   # inform taxis that the fare abandoned
                   self._parent.cancelFare(origin, self._taxis[self._fareBoard[origin][destination][calltime].taxi])
                   del self._fareBoard[origin][destination][calltime]
                if len(self._fareBoard[origin][destination]) == 0:
                   del self._fareBoard[origin][destination]
                if len(self._fareBoard[origin]) == 0:
                   del self._fareBoard[origin]

      # taxis register their bids for a fare using this mechanism
      def fareBid(self, origin, taxi):
          # rogue taxis (not known to the dispatcher) can't bid on fares
          if taxi in self._taxis:
             # everyone else bids on fares available
             if origin in self._fareBoard:
                for destination in self._fareBoard[origin].keys():
                    for time in self._fareBoard[origin][destination].keys():
                        # as long as they haven't already been allocated
                        if self._fareBoard[origin][destination][time].taxi == -1:
                           self._fareBoard[origin][destination][time].bidders.append(self._taxis.index(taxi))
                           # only one fare per origin can be actively open for bid, so
                           # immediately return once we[ve found it
                           return
                     
      # fares call this (through the parent world) when they have reached their destination
      def recvPayment(self, parent, amount):
          # don't take payments from dodgy alternative universes
          if self._parent == parent:
             self._revenue += amount

      #________________________________________________________________________________________________________________

      # clockTick is called by the world and drives the simulation for the Dispatcher. It must, at minimum, handle the
      # 2 main functions the dispatcher needs to run in the world: broadcastFare(origin, destination, price) and
      # allocateFare(origin, taxi).
      def clockTick(self, parent):
          if self._parent == parent:
             for origin in self._fareBoard.keys():
                 for destination in self._fareBoard[origin].keys():
                     # TODO - if you can come up with something better. Not essential though.
                     # not super-efficient here: need times in order, dictionary view objects are not
                     # sortable because they are an iterator, so we need to turn the times into a
                     # sorted list. Hopefully fareBoard will never be too big
                     for time in sorted(list(self._fareBoard[origin][destination].keys())):
                         if self._fareBoard[origin][destination][time].price == 0:
                            self._fareBoard[origin][destination][time].price = self._costFare(self._fareBoard[origin][destination][time])
                            # broadcastFare actually returns the number of taxis that got the info, if you
                            # wish to use that information in the decision over when to allocate
                            self._parent.broadcastFare(origin,
                                                       destination,
                                                       self._fareBoard[origin][destination][time].price)
                         elif self._fareBoard[origin][destination][time].taxi < 0 and len(self._fareBoard[origin][destination][time].bidders) > 0:
                              self._allocateFare(origin, destination, time)

      #----------------------------------------------------------------------------------------------------------------

      ''' HERE IS THE PART THAT YOU NEED TO MODIFY
      '''

      '''this internal method should decide a 'reasonable' cost for the fare. Here, the computation
         is trivial: add a fixed cost (representing a presumed travel time to the fare by a given
         taxi) then multiply the expected travel time by the profit-sharing ratio. Better methods
         should improve the expected number of bids and expected profits. The function gets all the
         fare information, even though currently it's not using all of it, because you may wish to
         take into account other details.
      '''
      def _routeDistance(self, start, end):
          """Return shortest known road distance, or infinity if disconnected."""
          if start is None or end is None:
             return float("inf")
          if start == end:
             return 0.0
          if not self._map or start not in self._map:
             # Compatibility fallback for an incomplete dispatcher map.
             try:
                a = self._parent.getNode(start[0], start[1])
                b = self._parent.getNode(end[0], end[1])
                if a is None or b is None:
                   return float("inf")
                return float(self._parent.distance2Node(a, b))
             except (AttributeError, KeyError, TypeError, ValueError):
                return float("inf")
          distances = {start: 0.0}
          queue = [(0.0, start)]
          while queue:
             distance, node = heapq.heappop(queue)
             if distance != distances.get(node):
                continue
             if node == end:
                return distance
             for neighbour, edge in self._map.get(node, {}).items():
                try:
                   weight = float(edge[1]) if isinstance(edge, (tuple, list)) else float(edge)
                except (TypeError, ValueError, IndexError):
                   continue
                if weight < 0:
                   continue
                candidate = distance + weight
                if candidate < distances.get(neighbour, float("inf")):
                   distances[neighbour] = candidate
                   heapq.heappush(queue, (candidate, neighbour))
          return float("inf")

      def _costFare(self, fare):
          """Return a bounded quote based on the world travel-time estimate.

          The taxi keeps 90% of the gross price. The target therefore gives the
          taxi a fixed contribution above the estimated passenger-trip time,
          while the cap protects customers against extreme quotes.
          """
          origin_node = self._parent.getNode(fare.origin[0], fare.origin[1])
          destination_node = self._parent.getNode(fare.destination[0], fare.destination[1])
          estimated_time = self._parent.travelTime(origin_node, destination_node)
          if estimated_time < 0:
             estimated_time = self._routeDistance(fare.origin, fare.destination)
          if not math.isfinite(float(estimated_time)):
             estimated_time = 25.0
          taxi_target = 23.0 + float(estimated_time)
          gross_quote = taxi_target / 0.9
          return round(max(10.0, min(120.0, gross_quote)), 2)

      def _allocateFare(self, origin, destination, time):
          """Allocate to a feasible bidder balancing approach time and fairness.

          Wait at least two ticks for bids, but no longer than four once a valid
          bid exists. Use road-network distance rather than straight-line distance.
          A small historical allocation penalty prevents the same nearby taxi from
          winning every fare when candidates are otherwise comparable.
          """
          elapsed = self._parent.simTime - time
          fare = self._fareBoard.get(origin, {}).get(destination, {}).get(time)
          if fare is None or fare.taxi >= 0:
             return
          if elapsed < self._minimumBidWait:
             return

          fare_node = self._parent.getNode(origin[0], origin[1])
          if fare_node is None:
             return

          # Deduplicate repeated bids, which fareBid may record on successive ticks.
          bidder_indices = sorted(set(fare.bidders))
          candidates = []
          active_count = sum(1 for taxi in self._taxis if getattr(taxi, 'onDuty', False))
          for taxi_idx in bidder_indices:
             if not isinstance(taxi_idx, int) or taxi_idx < 0 or taxi_idx >= len(self._taxis):
                continue
             taxi = self._taxis[taxi_idx]
             if not getattr(taxi, 'onDuty', False):
                continue
             location = getattr(taxi, 'currentLocation', None)
             if not isinstance(location, (tuple, list)) or len(location) < 2:
                continue
             start = (location[0], location[1])
             approach = self._routeDistance(start, origin)
             if not math.isfinite(approach):
                continue
             candidates.append((taxi_idx, taxi, approach))

          if not candidates:
             return

          valid_bidder_count = len(candidates)
          # If every currently on-duty taxi has supplied a valid bid, no extra
          # waiting is needed. Otherwise allow up to four ticks for more bids.
          all_have_bid = active_count > 0 and valid_bidder_count >= active_count
          if not all_have_bid and elapsed < self._maximumBidWait:
             return

          min_allocations = min((self._allocationCount.get(taxi, 0) for _, taxi, _ in candidates), default=0)
          fairness_weight = 2.5  # equivalent to a small approach-time preference
          ranked = []
          for taxi_idx, taxi, approach in candidates:
             prior_jobs = self._allocationCount.get(taxi, 0)
             fairness_penalty = fairness_weight * (prior_jobs - min_allocations)
             ranked.append((approach + fairness_penalty, approach, taxi_idx, taxi))
          ranked.sort(key=lambda item: (item[0], item[1], item[2]))
          _, _, winner_idx, winner = ranked[0]

          fare.taxi = winner_idx
          self._parent.allocateFare(origin, winner)
          self._allocationCount[winner] = self._allocationCount.get(winner, 0) + 1


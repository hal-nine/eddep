"""Elite Dangerous Data Explorer and Planner.

EDDEP is a tool for Elite Dangerous players to help them check their status,
maximize trade profits and find trading opportunities between visited systems.
Unlike other web applications which aggregate data from multiple users EDDEP
works only with systems the player has visited. This limits the options, but
ensures the freshest available trading data.

To use EDDEP you will need to have the Elite Dangerous Market Connector
installed on your gaming computer. EDMC is available here:

https://github.com/Marginal/EDMarketConnector/wiki

The systems.py script needs to be placed in the EDMC data directory. This
location is controlled by setting it in EDMC in preferences, the output tab
by changing the File Location parameter.

Once a few systems have been visited and their data files collected EDDEP can
be used as follows.

python3 ./systems.py clean

Note: If you add a shebang line on top of this file i.e.
#!/<local_path_to_python3_binary>/bin/python3 and chmod the file so its
executable i.e. chmod 755 systems.py than just invoking ./systems.py as
described in the remaining examples should start the script.

Cleanup data files, i.e. multiple visits to the same system will generate
multiple data files. This command will remove older versions. Useful for
housekeeping if a history of prices at a given system is not needed.

./systems.py list

Will print a list of data file currenntly available to EDDEP. Useful for
diagnostic purposes and to test the next command.

./systems.py visited

This will output the list of systems visited. It should reflect the above list.
Its main use is to serve as a quick copy source to input origin and target
parameters (-o -t) which most other commands need.

NOTE: EDDEP will try to figure out the name of the system-station pair from
a substring of it. So often times it will be enough to enter just 'Nourse'
instead of the full 'Esumindii.Nourse City'. Also note that for strings not
involving whitespace EDDEP does not need the string to be quoted.

./systems.py -o Nourse buy

Lists items available for sale at a given station, including price and
quantity.

./systems.py -o Nourse sell

Lists item demand and its respective price on the station. Both the buy and
sell command are useful as diagnostic commands. The two most useful commands
are the following.

./systems.py -o Nourse -t Camarda trade2

The trade2 command will output a table of profitable trades between the -o
origin station and -t target station. So if for example a mission has the
player go from station A to station B. Trade2 can be used to earn extra
credits on the side by selecting the most profitable trade possible between
a pair of stations.

./systems.py ferengi

This command is a reference to a trading species in the Star Trek series. For
more information on the Ferengi see: https://en.wikipedia.org/wiki/Ferengi

The command will output all the trades with a profit greater than a specified
amount with the flag -l )--lowest_profit). The default if --lowest_profit is
not specified is 500 credits. By running ferengi with successively higher
lowest profits one can easily find the most profitable trade within the stations
in their data directory. Volume information is also printed in the resulting
table, somtimes the most profitable trade will not have enough quantity of goods
and a less profitable one may actually return more profits given the volume
possible.

If the ferengi command does not output any results, try lowering --lowest_profit
to a value below the default 500 credits.
"""

import argparse
import glob
import logging
import os

HELP_TXT = """Command can be one of:

clean: cleanup older data files.
list: list all data files.
visited: lists all the locations visited.
buy: lists all items for sale on a location.
sell: lists all station buy prices at location.
trade2: lists possible trades between origin and target location.
ferengi: list high trades in known systems."""

LOGGER = logging.getLogger('systems.py')
LOGGER.setLevel(logging.DEBUG)
# create console handler
CH = logging.StreamHandler()
# Select desired logging level
CH.setLevel(logging.ERROR)
# Setup a formatter
FORMATTER = logging.Formatter('%(levelname)s %(asctime)s %(name)s:%(lineno)s] '
                              '%(message)s')
CH.setFormatter(FORMATTER)
# add ch to logger
LOGGER.addHandler(CH)


class SystemsException(Exception):
  """Systems Related Exceptions."""
  pass


class LocationException(SystemsException):
  """Location errors."""
  pass


class Utils:
  """Utilities class."""

  @classmethod
  def location_matcher(cls, location_snippet, locations):
    """Match first location in locations based on snippet."""
    matched_location = ''
    for location in locations:
      if location_snippet in location:
        print('%s setting location to: %s' % (location_snippet, location))
        matched_location = location
        break
    if not matched_location:
      print('No visited location matches {}.'.format(location_snippet))
      raise LocationException('Missing location.')
    LOGGER.debug('Matched location=%s', matched_location)
    return matched_location

  @classmethod
  def read_csv(cls, location, csv_files):
    """Return location's csv file contents as list of lines."""
    if not location:
      raise LocationException('Missing location.')
    for file in csv_files:
      if location in file:
        LOGGER.debug('Reading data from file: %s', file)
        with open(file) as csvfile:
          items = csvfile.readlines()
    # Skip the header only return items.
    return items[1:]


class Systems:
  """Class to encapsulate systems related data and methods."""

  def __init__(self):
    self.csv_files = glob.glob('*[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T'
                               '[0-9][0-9].[0-9][0-9].[0-9][0-9]*.csv')
    self.prices_files = glob.glob('*[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T'
                                  '[0-9][0-9].[0-9][0-9].[0-9][0-9]*.prices')
    self.locations_dict = {}
    self.locations = []
    self.most_recent_locations = []
    self._find_locations()
    if not os.path.exists('tmp'):
      os.makedirs('tmp')
    self.utils = Utils()

  def _find_locations(self):
    """Initialize locations dict and list."""
    for filename in self.csv_files:
      file_fields = filename.split('.')
      LOGGER.debug('file_fields=%r', file_fields)
      location = '%s.%s' % (file_fields[0], file_fields[1])
      if location not in self.locations_dict:
        self.locations_dict[location] = 1
    self.locations = sorted(list(self.locations_dict.keys()))

  def clean(self):
    """Remove all but newest csv and prices data files."""
    files = {}
    for file in self.csv_files:
      location, station, date = file.split('.', 2)
      location = '%s.%s' % (location, station)
      date = date.replace('.', '-', 2)
      date = date.replace('T', '-')
      date = date.split('.')[0]
      if location in files:
        prev_date = files[location]
        prev_tokens = prev_date.split('-')
        new_tokens = date.split('-')
        # Compare the dates components and select the date
        # with the bigger component
        for prev_token, new_token in zip(prev_tokens, new_tokens):
          if int(new_token) > int(prev_token):
            files[location] = date
            break
      else:
        # No previous record for this file
        files[location] = date
    # Fix dates back to filename form.
    for location in files:
      date = list(files[location])
      date[10] = 'T'
      date[13] = '.'
      date[16] = '.'
      file_date = ''.join(date)
      files[location] = file_date
      self.most_recent_locations.append('%s.%s' % (location, file_date))
      self.most_recent_locations.sort()
    LOGGER.debug(self.most_recent_locations)
    # Clean up csv files.
    for file in self.csv_files:
      if file.split('.csv')[0] not in self.most_recent_locations:
        print('Removing: %s' % file)
        os.remove(file)
      else:
        print('Keeping most recent: %s' % file)
    # Clean up prices files.
    for file in self.prices_files:
      if file.split('.prices')[0] not in self.most_recent_locations:
        print('Removing: %s' % file)
        os.remove(file)
      else:
        print('Keeping most recent: %s' % file)

  def visited(self):
    """Show all visited locations."""
    for location in self.locations:
      print(location)

  def list(self):
    """List all current data."""
    for data_file in self.csv_files:
      print(data_file)
    for data_file in self.prices_files:
      print(data_file)

  def list_goods_for_sale(self, location):
    """List goods for sale at station."""
    # Get full location name from snippet.
    location = self.utils.location_matcher(location, self.locations)
    # Match csv fil and get items.
    location_items = self.utils.read_csv(location, self.csv_files)
    if not location_items:
      return
    print('ITEM, LOCATION SELL PRICE, QUANTITY AVAILABLE - {}'.format(location))
    for item in location_items:
      columns = item.split(';')
      if columns[7]:
        print('{:30} {:>5} Cr {:>8} t'.format(columns[2], int(columns[4]),
                                              int(columns[7])))
  def list_goods_prices(self, location):
    """List which can be sold at station."""
    # Get full location name from snippet.
    location = self.utils.location_matcher(location, self.locations)
    # Match csv file and get items.
    location_items = self.utils.read_csv(location, self.csv_files)
    if not location_items:
      return
    print('ITEM, LOCATION Buy PRICE, DEMAND - {}'.format(location))
    for item in location_items:
      columns = item.split(';')
      print('{:30} {:>5} Cr {}'.format(columns[2], int(columns[3]),
                                       columns[6]))

  def trade2(self, origin, target):
    """List most profitable trade items between two locations."""
    LOGGER.debug('origin=%s, target=%s', origin, target)
    LOGGER.debug('systems.locations=%r', self.locations)
    LOGGER.debug(self.csv_files)
    # Get full location name from snippet.
    origin = self.utils.location_matcher(origin, self.locations)
    target = self.utils.location_matcher(target, self.locations)
    # Match csv file and get items.
    origin_items = self.utils.read_csv(origin, self.csv_files)
    target_items = self.utils.read_csv(target, self.csv_files)
    print('Origin location: {} Target location: {}'.format(origin, target))
    for o_item in origin_items:
      o_columns = o_item.split(';')
      for t_item in target_items:
        t_columns = t_item.split(';')
        # If the item is available for purchase in the origin system.
        # And its the same item on both systems.
        if o_columns[7] and o_columns[2] == t_columns[2]:
          sell_price = int(t_columns[3])
          buy_price = int(o_columns[4])
          profit = sell_price - buy_price
          if profit > 0:
            print('{:30} {:>5} cr {:>7} t supply'.format(
                o_columns[2], int(o_columns[4]), int(o_columns[7])), end='')
            print(' | sell@ {:>5} cr | Profit: {:>5}'.format(int(t_columns[3]), profit))

  def profits_for_station_pair(self, origin, target, lowest_profit):
    """Output profits between two stations"""
    origin_items = self.utils.read_csv(origin, self.csv_files)
    target_items = self.utils.read_csv(target, self.csv_files)
    for o_item in origin_items:
      o_columns = o_item.split(';')
      for t_item in target_items:
        t_columns = t_item.split(';')
        # If the item is available for purchase in the origin system.
        # And its the same item on both systems.
        if o_columns[7] and o_columns[2] == t_columns[2]:
          sell_price = int(t_columns[3])
          buy_price = int(o_columns[4])
          profit = sell_price - buy_price
          if profit > int(lowest_profit):
            print('{} ---> {}'.format(origin, target))
            print('{:30} {:>5} cr {:>7} t supply'.format(
                o_columns[2], int(o_columns[4]), int(o_columns[7])), end='')
            print(' | sell@ {:>5} cr | Profit: {:>5}'.format(
                int(t_columns[3]), profit))
          else:
            LOGGER.debug('Item: %s, Profit: %s', o_columns[2], profit)
            LOGGER.debug('Items not found with profit > %s Cr.',
                         lowest_profit)

  def high_trades(self, lowest_profit=500):
    """Find locations with highest trades between them."""
    # Iterate through all EDMC location pairs.
    print(self.locations)
    for origin in self.locations:
      for target in self.locations:
        if origin == target or origin == 'Shinrarta Dezhra.Jameson Memorial':
          continue
        else:
          self.profits_for_station_pair(origin, target, lowest_profit)


def main():
  """Elite Dangerous Data Explorer."""
  # Setup arguments.
  parser = argparse.ArgumentParser(
      description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('command',
                      help=HELP_TXT)
  parser.add_argument('-o', '--origin',
                      help='Starting location, can be substring of full name as'
                      ' long as its unambigous.')
  parser.add_argument('-t', '--to',
                      help='Target location, can be substring of full name as'
                      ' long as its unambigous.')
  parser.add_argument('-l', '--lowest_profit', default=500, help='Lowest profit'
                      ' allowable for the ferengi command.')
  args = parser.parse_args()
  # Load systems
  systems = Systems()
  # Process commands
  if args.command == 'clean':
    systems.clean()
  if args.command == 'visited':
    systems.visited()
  if args.command == 'list':
    print('System List:')
    systems.list()
  if args.command == 'trade2':
    if not args.origin or not args.to:
      print('Please pecify origin and destination snippets. Run with -h for help.')
      exit()
    systems.clean()
    systems = Systems()
    systems.trade2(args.origin, args.to)
  if args.command == 'buy':
    if not args.origin:
      print('Please specify origin snippet. Run with -h for help.')
      exit()
    systems.list_goods_for_sale(args.origin)
  if args.command == 'sell':
    if not args.origin:
      print('Please specify origin snippet. Run with -h for help.')
      exit()
    systems.list_goods_prices(args.origin)
  if args.command == 'ferengi':
    systems.high_trades(args.lowest_profit)


if __name__ == "__main__":
  try:
    main()
  except LocationException:
    print('Location Error. Aborting.')

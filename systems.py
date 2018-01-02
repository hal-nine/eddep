#!/Users/debic/anaconda/bin/python3
"""Elite Dangerous Data Explorer."""

import argparse
import glob
import logging
import os

HELP_TXT = """Command can be one of:

clean: cleanup older data files.
list: list all data files.
visited: lists all the locations visited.
buy: lists all items for sale on a location."""

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
        print('{:25} {:>5} Cr {:>8} t'.format(columns[2], int(columns[4]),
                                              int(columns[7])))

  def trade2(self, origin, target):
    """List most profitable trade items between two locations."""
    LOGGER.debug('origin=%s, target=%s', origin, target)
    LOGGER.debug('systems.locations=%r', self.locations)
    LOGGER.debug(self.csv_files)
    # Get full location name from snippet.
    origin = self.utils.location_matcher(origin, self.locations)
    target = self.utils.location_matcher(target, self.locations)
    # Match csv fil and get items.
    origin_items = self.utils.read_csv(origin, self.csv_files)
    target_items = self.utils.read_csv(target, self.csv_files)
    for item in target_items:
      columns = item.split(';')
      if columns[7]:
        print('{}: {} cr {} t supply'.format(columns[2], int(columns[4]), int(columns[7])))


def main():
  """Elite Dangerous Data Explorer."""
  # Setup arguments.
  parser = argparse.ArgumentParser(
      description='Elite Dangerous Data Explorer.', formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('command',
                      help=HELP_TXT)
  parser.add_argument('-o', '--origin',
                      help='Starting location, can be substring of full name as'
                      ' long as its unambigous.')
  parser.add_argument('-t', '--to',
                      help='Target location, can be substring of full name as'
                      ' long as its unambigous.')
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
    systems.trade2(args.origin, args.to)
  if args.command == 'buy':
    if not args.origin:
      print('Please specify origin snippet. Run with -h for help.')
      exit()
    systems.list_goods_for_sale(args.origin)

if __name__ == "__main__":
  try:
    main()
  except LocationException:
    print('Location Error. Aborting.')

# eddep
Elite Dangerous Data Explorer and Planner

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

./systems.py clean

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

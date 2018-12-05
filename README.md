# Multi-Agent Traffic Simulation
The dataset contains the car owners' demand in a 10x10 grid structured city for two different scenarios.
Every car start at a certain node on the map, and aims to reach a destination node. 
The dataset also contains the desired starting time for every agent.

## Format of the datasets
Every row is associated with an agent

-'Agent' column - the unique id of the corresponding agent
-'Start' column - the unique id of the starting node on the map for the corresponding agent
-'Dest' column - the unique id of the desired destination node on the map for the corresponding agent
-'Time' column - the starting time of the agent in seconds (the simulation starts at time 0)

### Case 1
In this scenario agents are randomly generated over the map, with random destinations varying
from the shortest to the longest routes. 
	 
### Case 2	 
In this scenario we assumed, that there are 2 big clusters of living areas in the city, 
one at the top left, and one at the bottom left corner of the grid structured map. Cars
starting at the top left corner are aiming for the bottom right corner destination area,
while the ones coming from the bottom left, heading towards points at the top right.
The described areas are spreaded out in a given radius, and agents are randomly generated.
The scenario is aiming to create a busy network where the two main paths cross each other,
and therefore test the optimization algorithm in heavy traffic.




# coding: utf-8

# # Route Generator
#
# ## Inputs
# - File containing the road network
# - File containing the link parameters such as travel time, waiting time, toll fare.
# - File containing the position, destination for each agent
# - File containing the agent parameters
#
# ## Outputs
# - File containing plans for all agents with scores

# In[1]:


import networkx as nx
from matplotlib import pyplot as plt
import numpy as np
import random
import os
import xml.etree.ElementTree as et
import csv
import re
import argparse
from kspath.deviation_path.mps import SingleTargetDeviationPathAlgorithm

# ### Helper Functions

# In[2]:


def drawNetwork(G, show_edge_information=True):
    '''
    Helper function to plot the network for visualization
    
    Return values:
        G - road network as a networkx graph
    '''
    pos = nx.get_node_attributes(G, 'pos')
    plt.figure(figsize=(12, 12))
    nx.draw(G, pos, labels={node: node for node in G.nodes()}, node_color='g')
    if show_edge_information:
        edge_labels = {
            (a, b):
            "%.2f" % round(nx.get_edge_attributes(G, 'p_1')[(a, b) if a < b else (b, a)], 2) + ', ' +
            "%.2f" % round(nx.get_edge_attributes(G, 'p_2')[(a, b) if a < b else (b, a)], 2) + ', ' +
            "%.2f" % round(nx.get_edge_attributes(G, 'p_3')[(a, b) if a < b else (b, a)], 2) + ', ' +
            "%.2f" % round(nx.get_edge_attributes(G, 'p_4')[(a, b) if a < b else (b, a)], 2) + '\n' +
            "%.2f" % round(nx.get_edge_attributes(G, 'p_1')[(a, b) if a > b else (b, a)], 2) + ', ' +
            "%.2f" % round(nx.get_edge_attributes(G, 'p_2')[(a, b) if a > b else (b, a)], 2) + ', ' +
            "%.2f" % round(nx.get_edge_attributes(G, 'p_3')[(a, b) if a > b else (b, a)], 2) + ', ' +
            "%.2f" % round(nx.get_edge_attributes(G, 'p_4')
                           [(a, b) if a > b else (b, a)], 2)
            for a, b in G.edges()}
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=edge_labels, font_color='r')
    plt.axis('off')
    plt.show()


# ### Parameters

# In[3]:


n_params = 4  # No. of link parameters
n_plans = 16  # No. of plans per agent
interval = 5*60  # Number of seconds each iteration
max_time_per_plan = 5*60  # Number of seconds to generate plans for

dataset_path = '../output/traffic/'
completed_trips_file = '../output/complete.txt'

parser = argparse.ArgumentParser()
parser.add_argument('--netstate_output',
                    help='the output file from last itaration - netstate-output.xml file')
parser.add_argument('--trips', help='the trips file - trips.csv file')
parser.add_argument(
    '--preferences', help='the preferences file - preferences.csv file')
parser.add_argument('--node', help='the node file - ***.nod.xml file')
parser.add_argument('--edge', help='the edge file - ***.edg.xml file')
parser.add_argument('--current_time', help='current time in seconds')
parser.add_argument('--link_file', help='file containg link parameters')
parser.add_argument('--first_file', help='file containg first link parameters')

args = parser.parse_args()

nodes_file = args.node
edges_file = args.edge
prefs_file = args.preferences
trips_file = args.trips
last_pos_file = args.netstate_output
current_time = int(args.current_time)
link_file = args.link_file
first_file = args.first_file

# nodes_file = '../config/SUMO/testNewGrid.nod.xml'
# edges_file = '../config/SUMO/testNewGrid.edg.xml'
# prefs_file = '../config/Agents/preferences.csv'
# trips_file = '../config/Agents/trips.csv'
# last_pos_file = '../config/SUMO/netstate-outputNewGrid.xml'
# current_time = 0*60


# ### Core Functionality

# In[4]:


def getNetworkFromFile(path):
    '''
    Creates a network using the networkx library using the file containing the road network
    
    Parameters:
        path    - path to input file containing road network
    
    Return values:
        G       - graph of networkx which contains the road network 
        n_nodes - number of nodes read
    '''

    root = et.parse(path).getroot()

    G = nx.DiGraph()

    for child in root:
        G.add_node(child.attrib['id'],
                   pos=(int(child.attrib['x']), int(child.attrib['y'])))

    n_nodes = len(root.getchildren())

    return G, n_nodes


# In[5]:


def getNetworkWithLinkParameters(G, path, link_file):
    '''
    Adds the link parameters (waiting time, travel time, etc to the road network)
    
    Parameters:
        G         - input road network as a networkx graph
        path      - path to input file containing network parameters
        link_file - file containing link parameters 
    Return values:
        G         - road network with parameters added
        n_links   - number of links read
    '''

    n_links = 0
    root = et.parse(path).getroot()
    edges = {}

    if current_time==0:
        link_file = first_file
        
    
    for child in root:
        edges[child.attrib['id']] = {}
        edges[child.attrib['id']]['from'] = child.attrib['from']
        edges[child.attrib['id']]['to'] = child.attrib['to']
        edges[child.attrib['id']]['easy_link_id'] = n_links
        n_links = n_links + 1
    
    with open(link_file, mode='r') as infile:
        reader = csv.reader(infile)
        next(reader)
        
        for row in reader:
            edges[row[0]]['travel']=float(row[1])
            edges[row[0]]['waiting']=float(row[2])
            edges[row[0]]['fuel']=float(row[3])
            edges[row[0]]['toll']=float(row[4])
    
    for edge in edges:
        this_edge = edges[edge]
        G.add_edge(this_edge['from'], this_edge['to'],
                   link_id=edge,
                   easy_link_id=this_edge['easy_link_id'],
                   p_1=this_edge['travel'],
                   p_2=this_edge['waiting'],
                   p_3=this_edge['fuel'],
                   p_4=this_edge['toll'])

    return G, n_links


# In[6]:


def getAgentPreferencesFromFile(path):
    '''
    Read preferences of all agents from file
    
    Parameters:
        path        - path to input file containing preferences
        
    Return values:
        agent_prefs - dict containing preferences for each agents
        n_prefs     - no of preferences read
    '''

    with open(path, mode='r') as infile:
        reader = csv.reader(infile)
        num_vals = len(next(reader)) - 1
        agent_prefs = {rows[0]: {
            'w_'+str(i+1): float(rows[i+1]) for i in range(num_vals)} for rows in reader}

    n_prefs = len(agent_prefs)

    return agent_prefs, n_prefs


# In[7]:


def getTripsFromFile(path):
    '''
    Read trips of all agents from file
    
    Parameters:
        path          - path to input file containing all trips
        
    Return values:
        agent_trips   - list containing trips for each agent
        n_trips       - number of trips read
    '''

    with open(path, mode='r') as infile:
        reader = csv.reader(infile)
        num_vals = len(next(reader)) - 1
        agent_trips = {rows[0]: {'start': int(rows[1]), 'dest': int(
            rows[2]), 'time': round(float(rows[3]))} for rows in reader}

    n_trips = len(agent_trips)

    return agent_trips, n_trips


# In[8]:


def getCompletedTripsFromFile(path):
    '''
    Inputs file which has positions of agents output from SUMO
    
    Parameters:
        path            - path to file
        
    Return values:
        completed_trips - list read from file
    '''

    completed_trips = []
    if current_time != 0:
        with open(path) as f:
            completed_trips = f.readlines()
        completed_trips = [x.strip() for x in completed_trips]

    return completed_trips


# In[9]:


def getAgentPositionsFromFile(path):
    '''
    Inputs file which has list of agents which completed
    their trips upto the previous iteration
    
    Parameters:
        path            - path to file containing said list
        
    Return values:
        agent_locs      - agent locations from file
        completed_trips - list of agents which completed trips
    '''

    global interval, current_time

    completed_trips = []
    agent_locs = {}

    if current_time == 0:
        return agent_locs, completed_trips

    root = et.parse(last_pos_file).getroot()

    # First find all agents that appear sometime between last_start-last_end
    agent_set = set()
    for i in range(current_time-interval, current_time):
        for v in root.findall(".//*[@time='%.02f']//vehicle" % i):
            agent_set.add(v.get('id'))

    agent_set_still_existing = set()
    for v in root.findall(".//*[@time='%.02f']//vehicle" % current_time):
        agent_set_still_existing.add(v.get('id'))

    for e in root.findall(".//*[@time='%.02f']/edge" % current_time):
        for v in e.findall(".//vehicle"):
            if e.get('id')[0] != ':':  # when agent is at node
                agent_locs[v.get('id')] = re.search(
                    'e(.*)-', e.get('id')).group(1)

    completed_trips = list(agent_set - agent_set_still_existing)

    return agent_locs, completed_trips


# In[10]:


def getPlansForTrips(G, agent_trips, agent_prefs, n_links, completed_trips):
    '''
    Inputs trips and generates plans
    
    Parameters:
        G               - road network as a networkx graph
        agent_trips     - list containing trips for all agents 
        agent_prefs     - dict containing agent preferences
        n_links         - number of links in the road network 
        completed_trips - list of agents with trips completed
        
    Return values:
        plans           - dict containing plans for each agent
    '''

    # Plan structure is shown below
    # plans = {'agent_1':{'plan_1':[0,0,1,0,1,0,0],
    #                     'plan_2':[0,1,0,0,0,1,0],
    #                     'plan_3':[0,0,1,0,0,0,1],
    #                     'plan_4':[1,0,0,0,1,0,0],
    #                     'cost_1':1.34,
    #                     'cost_2':1.07,
    #                     'cost_3':1.71,
    #                     'cost_4':1.92},
    #          'agent_2':{'plan_1':[0,0,1,0,1,0,0],
    #                     'plan_2':[0,1,0,0,0,1,0],
    #                     'plan_3':[0,0,1,0,0,0,1],
    #                     'plan_4':[1,0,0,0,1,0,0],
    #                     'score_1':1.34,
    #                     'score_2':1.07,
    #                     'score_3':1.71,
    #                     'score_4':1.92},
    #          ... }

    global n_params, n_plans

    plans = {}

    plan = [0] * n_links  # plan = [0 0 0 0 ... 0]

    ids = nx.get_edge_attributes(G, 'easy_link_id')

    
    params = {}
    for i in range(n_params):
        params['p_'+str(i+1)] = nx.get_edge_attributes(G, 'p_'+str(i+1))

    for agent_id, agent_trip in agent_trips.items():

        plans[agent_id] = {}

        # getting preferences for current agent
        this_prefs = agent_prefs[agent_id]

        this_costs = {edge:0 for edge in params['p_1']} # {(i,j):0, ...}
        for i in range(n_params):
            this_costs = {edge:this_costs[edge] + \
            agent_prefs[agent_id]['w_%d'%(i+1)]*params['p_%d'%(i+1)][edge] \
            for edge in this_costs}
        
        nx.set_edge_attributes(G, name='cost', values=this_costs)

        dpa_mps = SingleTargetDeviationPathAlgorithm.create_from_graph(
            G=G, target='n%d' % agent_trip['dest'], weight='cost')
        
        paths = []
        
        # generate plans if agent is present in next iteration
        if agent_id not in completed_trips and agent_trip['time'] < current_time + max_time_per_plan:
            
            for path_count, path in enumerate(dpa_mps.shortest_simple_paths(source='n%d' % agent_trip['start']), 1):
                paths.append(path)
                if path_count == n_plans:
                    break
        
            for i in range(len(paths)):
                path = paths[i]
                # creating a copy of template
                this_plan = list(plan)

                this_score = 0

                this_time = agent_trip['time']

                for j in range(len(path)-1):
                    # setting my_plan[link_id] = 1 if link used
                    this_link = (path[j], path[j+1])

                    # The time for the plan so far is checked and the edge is set to 1
                    # only if it is being used in the next max_time_per_plan time units
                    # The plan cost is also calculated for the same

                    if this_time < current_time + max_time_per_plan:
                        this_plan[ids[this_link]] = 1
                    
                        # adding time
                        this_time += params['p_1'][this_link]
                    
                        # adding link costs weighted with preferences to score
                        for k in range(n_params):
                            this_score += params['p_%d'%(k+1)][this_link] * this_prefs['w_%d'%(k+1)]

                plans[agent_id]['plan_%d'%(i+1)] = this_plan
                plans[agent_id]['score_%d'%(i+1)] = this_score
        else:
            for i in range(n_plans):
                plans[agent_id]['plan_%d'%(i+1)] = list(plan)
                plans[agent_id]['score_%d'%(i+1)] = 0
        
    return plans


# In[11]:


def writePlansToFiles(dataset_path, plans):
    '''
    Writes agent plans to file
    
    Parameters:
        dataset_path - path to write the plans
        plans        - agent plans
    
    Return values:
        None
    '''
    global n_plans

    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)
    for agent in plans:
        filename = agent + '.plans'
        with open(os.path.join(dataset_path, filename), 'w') as f:
            this_plans = []
            for i in range(1,n_plans+1):
                cost = 1333*plans[agent]['score_'+str(i)]
                if cost!=0:
                    cost += 10e-7*i
                plan_str = ','.join(map(str, plans[agent]['plan_'+str(i)]))
                this_plans.append([cost,plan_str])
            
            for plan in sorted(this_plans,key=lambda x: x[0]):
                f.write(str(plan[0])+":"+plan[1]+"\n")
            
            f.close()

# In[12]:


def writeCompletedTripsToFile(completed_trips, path):
    '''
    Writes agents with completed trips to file
    
    Parameters:
        completed_trips - list of agents with completed trips
        path            - path to file 
    
    Return values:
        None
    '''

    global current_time

    with open(path, 'w') as f:
        for agent in completed_trips:
            f.write(agent+'\n')


# ### Main Script

# In[13]:


G, n_nodes = getNetworkFromFile(nodes_file)
print('Generating road network with', n_nodes, 'nodes')


# In[14]:


G, n_links = getNetworkWithLinkParameters(G, edges_file, link_file)
print('Added', n_links, 'links to the network')


# In[15]:


agent_prefs, n_prefs = getAgentPreferencesFromFile(prefs_file)
print(n_prefs, 'preferences read from file')


# In[16]:


agent_trips, n_trips = getTripsFromFile(trips_file)
print(n_trips, 'trips read from file')


# In[17]:


completed_trips_prev = getCompletedTripsFromFile(completed_trips_file)
print('%d agents had completed their trips before the last iteration!' %
      len(completed_trips_prev))


# In[18]:


agent_locs, completed_trips = getAgentPositionsFromFile(last_pos_file)
print('%d agents completed their trips in the last iteration!' %
      len(completed_trips))


# In[19]:


agent_plans = getPlansForTrips(
    G, agent_trips, agent_prefs, n_links, completed_trips + completed_trips_prev)
print("Plans generated!")

# In[20]:


writePlansToFiles(dataset_path, agent_plans)
print("Wrote generated plans to: " + dataset_path)


# In[21]:


writeCompletedTripsToFile(
    completed_trips + completed_trips_prev, completed_trips_file)


# In[22]:


# drawNetwork(G, show_edge_information=False)

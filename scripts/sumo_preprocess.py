import os
import csv
from xml.dom import minidom
from xml.etree import ElementTree as ET
from itertools import compress
import numpy as np
import argparse

#PARAMETERS

parser=argparse.ArgumentParser()

parser.add_argument('--selected_plans',help='selected plans of the agents - selected-plans.csv file')
parser.add_argument('--plans',help='folder of the agent plans - folder full of agent_#.plans files')
parser.add_argument('--netstate_output',help='the output file from last itaration - netstate-output.xml file')
parser.add_argument('--trips',help='the trips file - trips.csv file')
parser.add_argument('--edge',help='the edge file - ***.edg.xml file')
parser.add_argument('--route',help='the route file - ***.rou.xml file')
parser.add_argument('--current_time',help='current time in seconds')

args=parser.parse_args()

path_csv=args.selected_plans
path_agents=args.plans
path_first_run=args.trips
path_output=args.netstate_output
path_edg=args.edge
path_rou=args.route
current_time=int(args.current_time)
stop_timestep='%.2f'%current_time
FIRST_IT=current_time==0.0

#path_scr=str(os.path.dirname(os.path.realpath(__file__)))
#path_rel_csv="\\files\\selected-plans.csv"
#path_rel_agents="\\files\\plans"
#path_rel_output="\\files\\netstate-output.xml"
#path_rel_first_run="\\files\\trips.csv"
#path_rel_edg="\\files\\testNewGrid.edg.xml"
#path_rel_rou="\\files\\testNewGrid.rou.xml"
#FIRST_IT=True
#stop_timestep='300.00'

#import csv file
 
agent_plans={}

with open(path_csv,"r") as csv_file:

    reader=csv.reader(csv_file,delimiter=',')

    for row in reader:
        last=row

    plan_ids=list(map(int,last[2:len(last)]))

    i=0
    for plan_id in plan_ids:
        agent_plans['agent_'+str(i)]={}
        agent_plans['agent_'+str(i)]['plan_id']=plan_id
        i=i+1

#import plans files

for agent in agent_plans:
    
    path_rel_agent_i=agent+".plans"
    path_agent_i=os.path.join(path_agents,path_rel_agent_i)
    
    with open(path_agent_i) as plans_i_file:
        for j, line in enumerate(plans_i_file):
            if j==agent_plans[agent]['plan_id']:
                # print agent, line
                plan_10_list=list(map(int,line.split(":")[1].split(",")))
                agent_plans[agent]['plan_10_list']=plan_10_list
                break

#import output file

with open(path_first_run,"r") as first_run_csv_file:

    reader=csv.reader(first_run_csv_file,delimiter=',')

    next(reader)

    i=0
    for row in reader:
        agent_plans['agent_'+str(i)]['depart']=row[-1]
        agent_plans['agent_'+str(i)]['pos']=0.00
        agent_plans['agent_'+str(i)]['speed']=0.00
        i=i+1

if not FIRST_IT:

    output_file=ET.parse(path_output)
    output_root=output_file.getroot()

    vehicles=output_root.findall(".//*[@time=\""+stop_timestep+"\"]//vehicle")

    for vehicle in vehicles:
        agent_plans[vehicle.get("id")]['depart']=stop_timestep
        agent_plans[vehicle.get("id")]['pos']=vehicle.get("pos")
        agent_plans[vehicle.get("id")]['speed']=vehicle.get("speed")

#import edge file

edge_file=ET.parse(path_edg)
edge_root=edge_file.getroot()

edges=edge_root.findall("edge")

#mask agents not yet/already not in the system

agent_plans_nonzero={}

for agent in agent_plans:
    if any(agent_plans[agent]['plan_10_list']):
        agent_plans_nonzero[agent]=agent_plans[agent]

#create routes

def domino_ordering(sorted_edges):

    list_len=len(sorted_edges)
    
    edges_list_id=[]
    edges_list_from=[]
    edges_list_to=[]

    for edge in sorted_edges:
        edges_list_id.append(edge.get("id"))
        edges_list_from.append(edge.get("from"))
        edges_list_to.append(edge.get("to"))

    first=list(set(edges_list_from)-set(edges_list_to))

    first=first[0]
    first_index=edges_list_from.index(first)

    route_index_list=[first_index]
    route_str=str(edges_list_id[first_index])

    for i in range(0,list_len-1):
        route_index_list.append(edges_list_from.index(edges_list_to[route_index_list[i]]))
        route_str=route_str+" "+str(edges_list_id[route_index_list[i+1]])

    return route_str

for agent in agent_plans_nonzero:
    agent_plans_nonzero[agent]['route_str']=domino_ordering(list(compress(edges,agent_plans[agent]['plan_10_list'])))
    
#export route file
sorted_by_value = sorted(agent_plans_nonzero.items(), key=lambda kv: float(kv[1]['depart']))
# print sorted_by_value

with open(path_rou,"w") as rou_file:

    rou_file.write("<routes>\n")
    rou_file.write('<vType id="Car" accel="1.0" decel="5.0" length="2.0" maxSpeed="100.0" sigma="0.0"/>\n<vType id="Bus" accel="0.5" decel="3.0" length="12.0" maxSpeed="10.0" sigma="0.0"/>\n')

    for agent,agent_dict in sorted_by_value:
        rou_file.write('<route id="r_'+agent+'" edges="'+agent_dict['route_str']+'"/>\n')
        rou_file.write('<vehicle id="'+agent+'" route="r_'+agent+'" pos="'+str(agent_dict['pos'])+'" speed="'+str(agent_dict['speed'])+'" depart="'+str(agent_dict['depart'])+'" type="Car"/>\n')

    rou_file.write("</routes>")

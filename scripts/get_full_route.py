import os
from xml.etree import ElementTree as ET
import argparse

#PARAMETERS - !!!!!!!!!!!!!!!!!

parser=argparse.ArgumentParser()

parser.add_argument('--output_folder',help='output folder - contains all output files')
parser.add_argument('--output_route',help='the path of the output file of this script - .rou.xml file')

args=parser.parse_args()

path=print(args.output_folder)
path_route="routes.rou.xml"
path_output_route=print(args.output_route)

#get directories

routes={}

for name in os.listdir(path):
    str_list=name.split('_')
    time=int(str_list[1])
    routes[time]={}
    routes[time]['dir']=os.path.abspath(os.path.join(path,name))

#concatenating edges

def Route_conc(dic_agent,agent_route_edges):
    #get route
    str_old=dic_agent.get('route_edges')
    str_new=agent_route_edges

    separator=" "
    list_str_old=str_old.split(separator)
    list_str_new=str_new.split(separator)

    #list_str_conc=list(set(list_str_old).difference(set(list_str_new)))+list_str_new

    for i in range(0,len(list_str_old)):
        nodes_old_i=list_str_old[i][1:].split("-")
        nodes_new_0=list_str_new[0][1:].split("-")

        if nodes_old_i[0]==nodes_new_0[0]:
            list_str_conc=list_str_old[0:i]+list_str_new
            break

        if nodes_old_i[1]==nodes_new_0[0]:
            list_str_conc=list_str_old[0:i+1]+list_str_new
            break
	
    str_conc=separator.join(list_str_conc)

    #get route_str
    route_str_new='<route id="'+dic_agent.get('route_id')+'" edges="'+str_conc+'"/>\n'

    dic_agent_new=dic_agent
    dic_agent_new['route_edges']=str_conc
    dic_agent_new['route_str']=route_str_new

    return dic_agent_new

#iterate over sorted time

agents={}

for key in sorted(routes):
    route_file=ET.parse(os.path.join(routes[key]['dir'],path_route))
    route_root=route_file.getroot()

    vehicles=route_root.findall(".//vehicle")

    for vehicle in vehicles:
        agent_id_str=vehicle.get('id')
        agent_num=agent_id_str.split('_')
        agent=int(agent_num[1])

        agent_route_id=vehicle.get('route')
        agent_route=route_root.findall(".//*[@id='"+agent_route_id+"']")
        agent_route=agent_route[0]
        agent_route_edges=agent_route.get('edges')

        if agent not in agents:
            agents[agent]={}

            agents[agent]['init_str']=ET.tostring(vehicle).decode('UTF-8')
            agents[agent]['route_str']=ET.tostring(agent_route).decode('UTF-8')
            agents[agent]['route_id']=agent_route.get('id')
            agents[agent]['route_edges']=agent_route_edges
        else:
            agents[agent]=Route_conc(agents[agent],agent_route_edges)

#create output route file - sorted by name
with open(path_output_route,"w") as rou_file:

    rou_file.write("<routes>\n")
    rou_file.write('<vType id="Car" accel="1.0" decel="5.0" length="2.0" maxSpeed="100.0" sigma="0.0"/>\n<vType id="Bus" accel="0.5" decel="3.0" length="12.0" maxSpeed="10.0" sigma="0.0"/>\n')

    for agent in sorted(agents):
        rou_file.write(agents[agent]['route_str'])
        rou_file.write(agents[agent]['init_str'])

    rou_file.write("</routes>")

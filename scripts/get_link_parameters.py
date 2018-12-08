import csv
import os
from xml.etree import ElementTree as ET
import argparse

#PARAMETERS

parser=argparse.ArgumentParser()

parser.add_argument('--sumo_output',help='the output file from sumo generated in the last iteration - edgeData-outputNewGrid.xml file')
parser.add_argument('--csv_in',help='the csv file containing link parameters from the last iteration - link#.csv file')
parser.add_argument('--csv_out',help='the csv file containing link parameters created and updated by this script - link#+1.csv file')

args=parser.parse_args()

path_sumo_output=args.sumo_output
path_csv_in=args.csv_in
path_csv_out=args.csv_out

#path_src=str(os.path.dirname(os.path.realpath(__file__)))

#path_sumo_output=path_src+'\edgeData-outputNewGrid.xml'
#path_csv_in=path_src+'\link.csv'
#path_csv_out=path_src+'\link_out.csv'


#Read csv in

with open(path_csv_in,"r") as csv_in:
    reader=csv.reader(csv_in,delimiter=',')
    next(reader)

    edges_csv={}

    for row in reader:
        edges_csv[row[0]]={}
        edges_csv[row[0]]['travel']=row[1]
        edges_csv[row[0]]['waiting']=row[2]
        edges_csv[row[0]]['fuel']=row[3]
        edges_csv[row[0]]['toll']=row[4]

    csv_in.close()

#Read sumo output

sumo_output=ET.parse(path_sumo_output)
sumo_output_root=sumo_output.getroot()

edges_info=sumo_output_root.findall(".//edge")

edges_sumo={}
for edge in edges_info:

    edge_id=edge.get('id')
    edges_sumo[edge_id]={}

    try:
        if edge.get('traveltime')!=None:
            edges_sumo[edge_id]['traveltime']=edge.get('traveltime')
        else:
            edges_sumo[edge_id]['traveltime']=0.001
    except KeyError:
        edges_sumo[edge_id]['traveltime']=0.001

    try:
        if edge.get('waitingTime')!=None:
            edges_sumo[edge_id]['waitingTime']=edge.get('waitingTime')
        else:
            edges_sumo[edge_id]['waitingTime']=0.001
    except KeyError:
        edges_sumo[edge_id]['waitingTime']=0.001

#Combine inputs

edges_comb=edges_csv

for edge in edges_sumo:
    print(edges_comb[edge]['travel'])
    print(edges_sumo[edge]['traveltime'])
    edges_comb[edge]['travel']=edges_sumo[edge]['traveltime']
    edges_comb[edge]['waiting']=edges_sumo[edge]['waitingTime']

#Write csv out

with open(path_csv_out,'wb') as csv_out:
    spamwriter=csv.writer(csv_out,delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(['Link','Travel','Waiting','Fuel','Toll'])
    for edge in edges_comb:
        spamwriter.writerow([edge,str(edges_comb[edge]['travel']),str(edges_comb[edge]['waiting']),str(edges_comb[edge]['fuel']),str(edges_comb[edge]['toll'])])

    csv_out.close()

#!/bin/bash

for i in `seq 0 300 6000`; do 
    echo Current time: $i; 
    python plan_generator.py --netstate_output ../output/netstate-output.xml --trips ../config/sample/trips.csv --preferences ../config/sample/preferences.csv --node ../config/sample/sample.nod.xml --edge ../config/sample/sample.edg.xml --current_time $i
    python sumo_preprocess.py --netstate_output ../output/netstate-output.xml --trips ../config/sample/trips.csv --edge ../config/sample/sample.edg.xml --current_time $i --route ../output/myout.rou.xml --selected_plans ../output/selected-plans.csv --plans ../output/traffic
    sumo -n ../config/sample/sample.net.xml -r ../output/myout.rou.xml --netstate-dump ../output/netstate-output.xml -b $i -e $((i+301))


done

#!/bin/bash

scenario="sample"
alpha="0.00"
beta="1.00"


GREEN='\033[0;32m'
NC='\033[0m' # No Color

outdir="../output/$scenario-$alpha-$beta" 
mkdir -p $outdir

for i in `seq 0 300 6000`; do 
    printf "${GREEN}Current time: $i ${NC}\n"
    
    mkdir $outdir/t_$i 
    
    # Run plan generator
    python plan_generator.py \
        --netstate_output $outdir/t_$((i-300))/netstate-output.xml \
        --trips ../config/$scenario/trips.csv \
        --preferences ../config/$scenario/preferences.csv \
        --node ../config/$scenario/$scenario.nod.xml \
        --edge ../config/$scenario/$scenario.edg.xml \
        --current_time $i
    
    # Run IEPOS
    cp -r ../output/traffic $outdir/t_$i/
    cp ../output/traffic/* ../I-EPOS/datasets/traffic
    cd ../I-EPOS
    sed_cmd="sed -i '36s/.*/weightsString = \"$alpha,$beta\"/' conf/epos.properties"
    eval $sed_cmd
    java -jar ../I-EPOS/IEPOS-Tutorial.jar
    mv `ls -td -- output/* | head -n 1`/* $outdir/t_$i
    cd ../scripts
    
    # Run SUMO preprocessing
    python sumo_preprocess.py \
        --netstate_output $outdir/t_$((i-300))/netstate-output.xml \
        --trips ../config/$scenario/trips.csv \
        --edge ../config/$scenario/$scenario.edg.xml \
        --route $outdir/t_$i/routes.rou.xml \
        --selected_plans $outdir/t_$i/selected-plans.csv \
        --plans $outdir/t_$i/traffic \
        --current_time $i
    
    # SUMO
    sumo \
        -n ../config/$scenario/$scenario.net.xml \
        -r $outdir/t_$i/routes.rou.xml \
        --netstate-dump $outdir/t_$i/netstate-output.xml \
        -b $i \
        -e $((i+301))
done

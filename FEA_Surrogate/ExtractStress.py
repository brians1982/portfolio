from odbAccess import *
from abaqusConstants import *
from odbMaterial import *
from odbSection import *

import os
import numpy as np


#Python 2.7 os.listdir() takes an arugment
files=os.listdir('.')


#Create list of odbs in directory
odbs=[]
for filename in files:
    file=filename.split('.')
    if file[1]=='odb':
        odbs.append(filename)



lines=[]
lines.append('jobid,xcoord,ycoord,zcoord,Mises\n')
for model in odbs:        
    #model=odbs[0]
    jobname=model.split('.')[0]

    odb=openOdb(path=model)
    
    #check if model ran successfully 
    if len(odb.steps.keys())==0:
        continue
        
    step = odb.steps.keys()[-1]
    frame=odb.steps[step].frames[-1]

    field = frame.fieldOutputs['S'].getSubset(position = ELEMENT_NODAL)

    #Values, labels correspond to Element Nodes - shared nodes appear multiple times
    Values=field.bulkDataBlocks[0].mises
    labels=field.bulkDataBlocks[0].nodeLabels

    #Unique node labels, idx of NodeLabels_unique in labels
    NodeLabels_unique, unq_idx = np.unique(labels, return_inverse=True)

    #Count of contributions at each node
    unq_counts = np.bincount(unq_idx)

    unq_sum = np.bincount(unq_idx, weights=Values)
    Values_Averaged = unq_sum / unq_counts

    #Get nodes in fillet
    fnodes = odb.rootAssembly.instances['PART-1-1'].nodeSets['FILLET'].nodes

    #Fillet node info - fn[node]={x:, y:, z:, Mises:}
    fn={}
    for fnode in fnodes:
        fn[fnode.label]={'x': fnode.coordinates[0], 
                                  'y':fnode.coordinates[1], 
                                  'z':fnode.coordinates[2]}
                                  
    #Add Stesses to dictionary for each node
    for key in fn.keys():
        fn[key]['Mises']=Values_Averaged[key-1]
        
        line = jobname + ',' + str(fn[key]['x']) + ',' + str(fn[key]['y']) + ','
        line = line + str(fn[key]['z']) + ',' + str(fn[key]['Mises']) + '\n'
        
        lines.append(line)
        
    odb.close()

file='stress_summary.csv'
dst=open(file, 'w')
dst.writelines(lines)
dst.close()
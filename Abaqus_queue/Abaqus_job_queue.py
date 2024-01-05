'''
Brian Shula
December, 2023

Utility to lanuch Abaqus jobs in batch that are in the same directory. The script finds all input decks, then checks to see if they have been run successfully, i.e., the jobs can be interrupted and restarted. If the .sta file indicates success, the job is not launched. If the .sta file is found but does not indicate success, the job is relaunched.

The script will run up to 'njobs' simultaneously, with ncpus.
'''

import os
import time


# simultaneous jobs
njobs = 2

# number of cpus 
ncpus=1

# lanuch command additions after 'abaqus job=file'
command =' cpus='+str(ncpus) + ' ask=off'

#success indication in .sta file
success='THE ANALYSIS HAS COMPLETED SUCCESSFULLY'

#delay to let job initialize, generate .lck file - avoid exceeding njobs
timedelay=5


def readsta(file):
    #function that determines if job completed from .sta file
    #Returns True if yes, False if no
    #
    try:
        src=open(file, 'r')
        lines=src.readlines()
        src.close()
        file=file.split('.')[0]
        #Not always last line - blank line can be at end
        for line in lines:
            if success in line:
                return True
        
        return False
    except:
        return False
            


# create list of files to run
inputs = []
files = os.listdir()
for file in files:
    if file.endswith('.inp'):
        file=file.split('.')[0]
        inputs.append(file)

#check if already completed
#find .sta file, if completed successfully, remove from inputs list
for file in files:
    if file.endswith('.sta'):
        if readsta(file):
            #if completed, remove from queue
            file=file.split('.')[0]
            idx=inputs.index(file)
            completed=inputs.pop(idx)
            print('Job ',completed,' already complete!')
        

#Run jobs that have not been completed
#Loop terminates when list of jobs reaches zero

#track jobs currently running
currentjobs=[]

while len(inputs) > 0 or len(currentjobs) > 0:
    # check for existing jobs running
    running = 0
    files = os.listdir()

    
    #determine number of jobs running
    for file in files:
        if file.endswith('.lck'):
            running = running + 1
            
    #determine if running job completed
    for job in currentjobs:
        if job+'.sta' in files:
            if readsta(job+'.sta'):
                idx=currentjobs.index(job)
                completed=currentjobs.pop(idx)
                print('Job ',completed,' finished!')
                
            
    
    #launch additional job if fewer than njobs running
    if running<njobs and len(inputs)>0: 
        job=inputs.pop(0)
        currentjobs.append(job)
        
        print('Running ', job,'...')
        submit='abaqus job='+job+command
        os.system(submit)
        
        #pause for enough time to generate the .lck file
        #may depend on license server latency
        time.sleep(timedelay)
    
    else:
        #check every 10 seconds for jobs to complete
        time.sleep(10)

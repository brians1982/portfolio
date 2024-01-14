#Import Libraries
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *

import time

def create_model(inputs):
    #inputs is a dictionary:
    #{'jobid': 'model0002', 'L1': 4.4968, 'L2': 5.8491, 'L3': 1.6841, 'L4': 2.3112, 'H1':1.2345, 'R1': 2.8127, 'R2': 0.6926}
    
    jobid = inputs['jobid']
    L1 = inputs['L1']
    L2 = inputs['L2']
    L3 = inputs['L3']
    L4 = inputs['L4']
    H1 = inputs['H1']
    R1 = inputs['R1']
    R2 = inputs['R2']
    
    #Some names used later
    modelname = 'beam_model'
    sketchname = 'beam_sketch'
    partname = 'Beam'
    instancename = 'Beam-1'
    caename = jobid + '.cae'
    beamsection = 'BeamSection'
    jobname = jobid

    #Global mesh size
    globalsize = 0.25

    #Create Model object and set Options
    model = mdb.Model(name=modelname)
    
    #Clear default model name
    if 'Model-1' in mdb.models.keys():
        del mdb.models['Model-1']
    
    model.setValues(noPartsInputFile=ON)

    #Create Sketch
    sketch = model.ConstrainedSketch(name=sketchname, sheetSize=20.0)

    #Boundary points
    p1 = (0.0, 0.0)
    p2 = (L2, 0.0)
    p3 = (L2, L3)
    p4 = (L4+R1, L3)
    p5 = (L4, L1)
    p6 = (0.0, L1)

    #Arc center
    p7 = (L4+R1, L1)

    #Hole ctr
    p8 = (L4, H1)

    #Pt on hole edge
    p9 = (L4+R2, H1)

    #Create lines and arc connection points; create hole as well
    Line1 = sketch.Line(point1=p1, point2=p6) 
    sketch.VerticalConstraint(addUndoState=False, entity=Line1)
        
    Line5 = sketch.Line(point1=p6, point2=p5)   
    sketch.HorizontalConstraint(addUndoState=False, entity=Line5)  
    sketch.PerpendicularConstraint(addUndoState=False, entity1=Line1, entity2=Line5)
        
    Line2 = sketch.Line(point1=p1, point2=p2)   
    sketch.HorizontalConstraint(addUndoState=False, entity=Line2)  
    sketch.PerpendicularConstraint(addUndoState=False, entity1=Line1, entity2=Line2)
        
    Line3 = sketch.Line(point1=p2, point2=p3)   
    sketch.VerticalConstraint(addUndoState=False, entity=Line3)   
    sketch.PerpendicularConstraint(addUndoState=False, entity1=Line2, entity2=Line3)
        
    Line4 = sketch.Line(point1=p3, point2=p4)
    sketch.HorizontalConstraint(addUndoState=False, entity=Line4)
    sketch.PerpendicularConstraint(addUndoState=False, entity1=Line3, entity2=Line4)
        
    Arc = sketch.ArcByCenterEnds(center=p7, direction=COUNTERCLOCKWISE, point1=p5, point2=p4)
        
    Hole = sketch.CircleByCenterPerimeter(center=p8, point1=p9)
        
    part = model.Part(dimensionality=TWO_D_PLANAR, 
        name=partname, type=DEFORMABLE_BODY)
     
    part.BaseShell(sketch=sketch)
        
    del sketch

    #Display resolution
    part.setValues(geometryRefinement=EXTRA_FINE)

    #Part Set for Section assignment
    region1=part.faces.findAt((p1[0], p1[1], 0))
    part.Set(faces=part.faces[region1.index:region1.index+1], name=partname)

    #Define linear elastic fictitious material    
    model.Material(name='Mat1')
    model.materials['Mat1'].Elastic(table=((1700000.0, 0.3), ))

    #Define Solid Section properties
    model.HomogeneousSolidSection(material='Mat1', 
        name=beamsection, thickness=1.5)

    #Assign Section properties    
    part.SectionAssignment(offset=0.0, 
        offsetField='', offsetType=MIDDLE_SURFACE, 
        region=part.sets[partname], sectionName=beamsection, 
        thicknessAssignment=FROM_SECTION)

    #Set up Assembly    
    model.rootAssembly.DatumCsysByDefault(CARTESIAN)

    #Bring Part into Assembly
    instance = model.rootAssembly.Instance(dependent=ON, 
        name=instancename, part=part)
    #Meshing in Assembly    
    model.rootAssembly.makeIndependent(instances=(instance, ))

    #Create Set for Hole edge
    region1=instance.edges.findAt((p9[0],p9[1],0))    
    model.rootAssembly.Set(name='Hole', 
        edges=instance.edges[region1.index:region1.index+1])

    #Create Set for Fillet edge 
    region1=instance.edges.findAt((p5[0],p5[1]-1e-5,0))     
    model.rootAssembly.Set(name='Fillet', 
        edges=instance.edges[region1.index:region1.index+1])  

    #Create Set for Fixed edge  
    midpt = (0.5*(p6[0]+p1[0]), 0.5*(p6[1]+p1[1]), 0)
    region1=instance.edges.findAt(midpt)   
    model.rootAssembly.Set(name='Fixed', 
        edges=instance.edges[region1.index:region1.index+1])


    #Create Set for Applied Force
    region1=instance.vertices.findAt((p3[0], p3[1], 0))  
    model.rootAssembly.Set(name='Force', 
        vertices=instance.vertices[region1.index:region1.index+1])

    #Surface for traction
    midpt = (0.5*(p2[0]+p3[0]), 0.5*(p2[1]+p3[1]), 0)
    region1=instance.edges.findAt(midpt) 
    model.rootAssembly.Surface(name='Traction', 
        side1Edges=instance.edges[region1.index:region1.index+1])
        
        
    #Create load step
    model.StaticStep(name='Bending', previous='Initial')

    #Fixed BC    
    model.DisplacementBC(amplitude=UNSET, createStepName='Initial', 
        distributionType=UNIFORM, fieldName='', localCsys=None, name='Fixed', 
        region=model.rootAssembly.sets['Fixed'], u1=SET, u2=SET, 
        ur3=UNSET)


    #Create Datum at midpoint of free edge, store ID    
    v1 = instance.vertices.findAt((p3[0], p3[1], 0))
    v2 = instance.vertices.findAt((p2[0], p2[1], 0))
    model.rootAssembly.DatumPointByMidPoint(point1=v1, point2=v2)
    datum_id=model.rootAssembly.datums.keys()[-1]

    #Create Reference Point, store ID 
    model.rootAssembly.ReferencePoint(point=model.rootAssembly.datums[datum_id])
    rp_id=model.rootAssembly.referencePoints.keys()[-1]

    #Reference Pt Set    
    model.rootAssembly.Set(name='RefPt', referencePoints=(
        model.rootAssembly.referencePoints[rp_id], ))

    #Distributed Coupling to RP    
    model.Coupling(controlPoint=model.rootAssembly.sets['RefPt'],
        couplingType=DISTRIBUTING, influenceRadius=WHOLE_SURFACE,
        localCsys=None, name='Coupling', surface=
        model.rootAssembly.surfaces['Traction'], u1=ON, u2=ON, ur3=ON, 
        weightingMethod=UNIFORM)

    #Apply load   
    model.ConcentratedForce(cf2=-1000.0, createStepName=
        'Bending', distributionType=UNIFORM, field='', localCsys=None, name=
        'BendLoad', region=model.rootAssembly.sets['RefPt'])   
        

    #Set element types
    region1=instance.faces.findAt((p1[0], p1[1], 0))
    model.rootAssembly.setElementType(elemTypes=(ElemType(
        elemCode=CPS8R, elemLibrary=STANDARD), ElemType(elemCode=CPS6M, 
        elemLibrary=STANDARD, secondOrderAccuracy=OFF, distortionControl=DEFAULT)), 
        regions=(instance.faces[region1.index:region1.index+1], ))

    #Mesh algorithm   
    model.rootAssembly.setMeshControls(algorithm=MEDIAL_AXIS, 
        elemShape=QUAD, 
        regions=instance.faces[region1.index:region1.index+1])


        
    #Local seed on fillet
    region1=instance.edges.findAt((p5[0],p5[1]-1e-5,0))   
    model.rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
        instance.edges[region1.index:region1.index+1], number=10)

    #Local seed on hole
    region1=instance.edges.findAt((p9[0],p9[1],0))   
    model.rootAssembly.seedEdgeByNumber(constraint=FINER, edges=
        instance.edges[region1.index:region1.index+1], number=20)    
    # model.rootAssembly.seedEdgeBySize(constraint=FINER, 
        # deviationFactor=0.1, 
        # edges=instance.edges[region1.index:region1.index+1], 
        # minSizeFactor=0.1, size=holesize)
        
        
    #Fifty opportunities to get below 1000 nodes - Model limitation
    #Gradually increase mesh seed sizes until reached
    for _ in range(50):
        #Set Global mesh size    
        model.rootAssembly.seedPartInstance(deviationFactor=0.1, 
            minSizeFactor=0.1, 
            regions=(instance, ), size=globalsize)

        #Crate mesh
        model.rootAssembly.generateMesh(regions=(instance, ))
        
        if len(instance.nodes) < 1000:
            break
        else:
            model.rootAssembly.deleteMesh(regions=(instance, ))
            globalsize = globalsize * 1.025
            
        
    #clear any old jobs
    for j in mdb.jobs.keys():
        del mdb.jobs[j]

    #Define current job options
    mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
        explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
        memory=90, memoryUnits=PERCENTAGE, model=modelname, modelPrint=OFF, name=
        jobname, nodalOutputPrecision=SINGLE, queue=None, resultsFormat=ODB, 
        scratch='', type=ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)

    #Save and write input
    mdb.saveAs(caename) 
    mdb.jobs[jobname].writeInput()

#Preprocess CSV information
file = 'model_definitions.csv'
src=open(file, 'r')
lines=src.readlines()
src.close()

#Dictionary to store model data
#Create dictionary of dictionaries from CSV:
#modeldata{'jobid':{'jobid':01, 'L1':xxx, 'L2:xxx,..}}
#Pandas not available in Abaqus 2023 or earlier
modeldata={}

#Header and example lines:
# jobid,L1,L2,L3,L4,H1,R1,R2
# model0000,4.2528,5.1383,2.4272,1.6085,2.6192,1.8256,0.3057
# model0001,4.0728,7.0055,2.7165,2.9818,2.7783,1.3563,0.2710

for line in lines:
    line=line.strip()
    #store headers
    if line.startswith('jobid'):
        headers=line.split(',')
        continue
    
    #data lines
    line = line.split(',')
    
    #initialize model sub-dictionary
    modeldata[line[0]]={}
    
    #Populate model sub-dictionary
    for i, data in enumerate(headers):
        if data == 'jobid':
            modeldata[line[0]][data] = line[i]
        else:
            modeldata[line[0]][data] = float(line[i])

#submit each sub-dictionary  
for key in modeldata.keys():
    print 'Creating model ' + key
    create_model(modeldata[key])
    

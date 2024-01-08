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

#Some names used later
modelname = 'beam_model'
sketchname = 'beam_sketch'
partname = 'Beam'
instancename = 'Beam-1'
caename = 'beam.cae'
beamsection = 'BeamSection'
jobname = 'Beam_Bending'

filletsize = 0.15
holesize = 0.17
globalsize = 0.25

#Create Model object and set Options
model = mdb.Model(name=modelname)
model.setValues(noPartsInputFile=ON)

#Create Sketch
sketch = model.ConstrainedSketch(name=sketchname, sheetSize=20.0)

#Boundary points
p1 = (0.0, 0.0)
p2 = (7.0, 0.0)
p3 = (7.0, 1.5)
p4 = (5.0, 1.5)
p5 = (3.5, 3.0)
p6 = (0.0, 3.0)

#Arc center
p7 = (5.0, 3.0)

#Hole ctr
p8 = (3.25, 1.25)

#Pt on hole edge
p9 = (3.75, 1.25)

#Create lines and arc connection points; create hole as well
L1 = sketch.Line(point1=p1, point2=p6) 
sketch.VerticalConstraint(addUndoState=False, entity=L1)
    
L5 = sketch.Line(point1=p6, point2=p5)   
sketch.HorizontalConstraint(addUndoState=False, entity=L5)  
sketch.PerpendicularConstraint(addUndoState=False, entity1=L1, entity2=L5)
    
L2 = sketch.Line(point1=p1, point2=p2)   
sketch.HorizontalConstraint(addUndoState=False, entity=L2)  
sketch.PerpendicularConstraint(addUndoState=False, entity1=L1, entity2=L2)
    
L3 = sketch.Line(point1=p2, point2=p3)   
sketch.VerticalConstraint(addUndoState=False, entity=L3)   
sketch.PerpendicularConstraint(addUndoState=False, entity1=L2, entity2=L3)
    
L4 = sketch.Line(point1=p3, point2=p4)
sketch.HorizontalConstraint(addUndoState=False, entity=L4)
sketch.PerpendicularConstraint(addUndoState=False, entity1=L3, entity2=L4)
    
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

# model.ConcentratedForce(cf2=-1000.0, createStepName='Bending', 
    # distributionType=UNIFORM, 
    # field='', localCsys=None, name='Force', 
    # region=model.rootAssembly.sets['Force'])

#Shear traction
#Points defining direction vector
v1 = instance.vertices.findAt((p3[0], p3[1], 0))
v2 = instance.vertices.findAt((p2[0], p2[1], 0)) 
#Create traction   
model.SurfaceTraction(createStepName='Bending', 
    directionVector=(v1, v2, distributionType=UNIFORM, 
    field='', localCsys=None, magnitude=1000.0, 
    name='SurfTraction', region=model.rootAssembly.surfaces['Traction'])

#Fixed BC    
model.DisplacementBC(amplitude=UNSET, createStepName='Initial', 
    distributionType=UNIFORM, fieldName='', localCsys=None, name='Fixed', 
    region=model.rootAssembly.sets['Fixed'], u1=SET, u2=SET, 
    ur3=UNSET)

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

#Fifty opportunities to get below 1000 nodes - Model limitation
#Gradually increase mesh seed sizes until reached
for _ in range(50):
    #Set Global mesh size    
    model.rootAssembly.seedPartInstance(deviationFactor=0.1, 
        minSizeFactor=0.1, 
        regions=(instance, ), size=globalsize)
    
    #Local seed on fillet
    region1=instance.edges.findAt((p5[0],p5[1]-1e-5,0))   
    model.rootAssembly.seedEdgeBySize(constraint=FINER, 
        deviationFactor=0.1, 
        edges=instance.edges[region1.index:region1.index+1], 
        minSizeFactor=0.1, size=filletsize)
        
    #Local seed on hole
    region1=instance.edges.findAt((p9[0],p9[1],0))       
    model.rootAssembly.seedEdgeBySize(constraint=FINER, 
        deviationFactor=0.1, 
        edges=instance.edges[region1.index:region1.index+1], 
        minSizeFactor=0.1, size=holesize)
        
    #Crate mesh
    model.rootAssembly.generateMesh(regions=(instance, ))
    
    if len(instance.nodes) < 1000:
        break
    else:
        model.rootAssembly.deleteMesh(regions=(instance, ))
        holesize = holesize * 1.01
        filletsize = filletsize * 1.001
        globalsize = globalsize * 1.025
        print globalsize, holesize, filletsize
    


mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
    explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
    memory=90, memoryUnits=PERCENTAGE, model='Model-1', modelPrint=OFF, name=
    'Beam_bending', nodalOutputPrecision=SINGLE, queue=None, resultsFormat=ODB, 
    scratch='', type=ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)


mdb.saveAs(caename) 
mdb.jobs[jobname].writeInput()

 

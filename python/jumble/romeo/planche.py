#_____________________________________________________________________________________________
#********************************************************************************************
#
#  Robot motion (romeo) using:
#  - ONLY OPERATIONAL TASKS
#  - Joint limits (position and velocity)
#_____________________________________________________________________________________________
#*********************************************************************************************

import sys
from optparse import OptionParser
from dynamic_graph import plug
from dynamic_graph.sot.core import *
from dynamic_graph.sot.core.math_small_entities import Derivator_of_Matrix
from dynamic_graph.sot.dynamics import *
from dynamic_graph.sot.dyninv import *
import dynamic_graph.script_shortcuts
from dynamic_graph.script_shortcuts import optionalparentheses
from dynamic_graph.matlab import matlab
from dynamic_graph.sot.core.meta_task_6d import toFlags
from dynamic_graph.sot.dyninv.meta_task_dyn_6d import MetaTaskDyn6d
from dynamic_graph.sot.dyninv.meta_tasks_dyn import *
from dynamic_graph.sot.core.utils.attime import attime
from numpy import *
from dynamic_graph.sot.dyninv.robot_specific import pkgDataRootDir,modelName,robotDimension,initialConfig,gearRatio,inertiaRotor, specificitiesName, jointRankName, postureRange
from dynamic_graph.sot.core.matrix_util import matrixToTuple, vectorToTuple,rotate, matrixToRPY
# from dynamic_graph.sot.core.utils.history import History
# from dynamic_graph.sot.dyninv.zmp_estimator import ZmpEstimator
from dynamic_graph.sot.core.utils.viewer_helper import addRobotViewer,VisualPinger

#-----------------------------------------------------------------------------
# --- ROBOT SIMU -------------------------------------------------------------
#-----------------------------------------------------------------------------

#robotName = 'hrp14small'
robotName = 'romeo'
robotDim  = robotDimension[robotName]
RobotClass = RobotDynSimu
robot      = RobotClass("romeo")
robot.resize(robotDim)
addRobotViewer(robot,small=True,small_extra=24,verbose=False)

# Similar initial position with hand forward
robot.set(initialConfig[robotName])

#-------------------------------------------------------------------------------
#----- MAIN LOOP ---------------------------------------------------------------
#-------------------------------------------------------------------------------

dt = 5e-3
def inc():
    robot.increment(dt)
    # Execute a function at time t, if specified with t.add(...)
#    if 'refresh' in ZmpEstimator.__dict__: zmp.refresh()
    attime.run(robot.control.time)
#    robot.viewer.updateElementConfig('zmp',[zmp.zmp.value[0],zmp.zmp.value[1],0,0,0,0])
    if dyn.com.time >0:
        robot.viewer.updateElementConfig('com',[dyn.com.value[0],dyn.com.value[1],0,0,0,0])
#    history.record()

from dynamic_graph.sot.core.utils.thread_interruptible_loop import loopInThread,loopShortcuts
@loopInThread
def loop():
#    try:
        inc()
#    except:
#        print robot.state.time,': -- Robot has stopped --'
runner=loop()

@optionalparentheses
def go(): runner.play()
@optionalparentheses
def stop(): runner.pause()
@optionalparentheses
def next(): inc()

attime.addPing( VisualPinger(robot.viewer) )

#-----------------------------------------------------------------------------
#---- DYN --------------------------------------------------------------------
#-----------------------------------------------------------------------------

modelDir  = pkgDataRootDir[robotName]
xmlDir    = pkgDataRootDir[robotName]
specificitiesPath = xmlDir + '/' + specificitiesName[robotName]
jointRankPath     = xmlDir + '/' + jointRankName[robotName]

dyn = Dynamic("dyn")
dyn.setFiles(modelDir, modelName[robotName],specificitiesPath,jointRankPath)
dyn.parse()

dyn.lowerJl.recompute(0)
dyn.upperJl.recompute(0)
llimit = matrix(dyn.lowerJl.value)
ulimit = matrix(dyn.upperJl.value)
dlimit = ulimit-llimit
mlimit = (ulimit+llimit)/2
llimit[6:18] = mlimit[6:12] - dlimit[6:12]*0.48
dyn.upperJl.value = vectorToTuple(ulimit)

dyn.inertiaRotor.value = inertiaRotor[robotName]
dyn.gearRatio.value    = gearRatio[robotName]

plug(robot.state,dyn.position)
plug(robot.velocity,dyn.velocity)
dyn.acceleration.value = robotDim*(0.,)

dyn.ffposition.unplug()
dyn.ffvelocity.unplug()
dyn.ffacceleration.unplug()

dyn.setProperty('ComputeBackwardDynamics','true')
dyn.setProperty('ComputeAccelerationCoM','true')

robot.control.unplug()

#-----------------------------------------------------------------------------
# --- OPERATIONAL TASKS (For HRP2-14)---------------------------------------------
#-----------------------------------------------------------------------------

# --- Op task for the waist ------------------------------
taskWaist = MetaTaskDyn6d('taskWaist',dyn,'waist','waist')
taskChest = MetaTaskDyn6d('taskChest',dyn,'chest','chest')
taskHead = MetaTaskDyn6d('taskHead',dyn,'head','gaze')
taskrh = MetaTaskDyn6d('rh',dyn,'rh','right-wrist')
tasklh = MetaTaskDyn6d('lh',dyn,'lh','left-wrist')
taskrf = MetaTaskDyn6d('rf',dyn,'rf','right-ankle')

for task in [ taskWaist, taskChest, taskHead, taskrh, tasklh, taskrf ]:
    task.feature.frame('current')
    task.gain.setConstant(50)
    task.task.dt.value = dt

# --- TASK COM ------------------------------------------------------
taskCom = MetaTaskDynCom(dyn,dt)

# --- TASK POSTURE --------------------------------------------------
taskPosture = MetaTaskDynPosture(dyn,dt)

# --- Task lim ---------------------------------------------------
taskLim = TaskDynLimits('taskLim')
plug(dyn.position,taskLim.position)
plug(dyn.velocity,taskLim.velocity)
taskLim.dt.value = dt

dyn.upperJl.recompute(0)
dyn.lowerJl.recompute(0)
taskLim.referencePosInf.value = dyn.lowerJl.value
taskLim.referencePosSup.value = dyn.upperJl.value

#dqup = (0, 0, 0, 0, 0, 0, 200, 220, 250, 230, 290, 520, 200, 220, 250, 230, 290, 520, 250, 140, 390, 390, 240, 140, 240, 130, 270, 180, 330, 240, 140, 240, 130, 270, 180, 330)
dqup = (1000,)*robotDim
taskLim.referenceVelInf.value = tuple([-val*pi/180 for val in dqup])
taskLim.referenceVelSup.value = tuple([val*pi/180 for val in dqup])

#-----------------------------------------------------------------------------
# --- SOT Dyn OpSpaceH: SOT controller  --------------------------------------
#-----------------------------------------------------------------------------

sot = SolverDynReduced('sot')
contact = AddContactHelper(sot)

sot.setSize(robotDim-6)
#sot.damping.value = 1e-2
sot.breakFactor.value = 10

plug(dyn.inertiaReal,sot.matrixInertia)
plug(dyn.dynamicDrift,sot.dyndrift)
plug(dyn.velocity,sot.velocity)

plug(sot.solution, robot.control)

#For the integration of q = int(int(qddot)).
plug(sot.acceleration,robot.acceleration)

#-----------------------------------------------------------------------------
# ---- CONTACT: Contact definition -------------------------------------------
#-----------------------------------------------------------------------------

# Left foot contact
contactLF = MetaTaskDyn6d('contact_lleg',dyn,'lf','left-ankle')
contactLF.feature.frame('desired')
contactLF.gain.setConstant(1000)
contactLF.name = "LF"

# Right foot contact
contactRF = MetaTaskDyn6d('contact_rleg',dyn,'rf','right-ankle')
contactRF.feature.frame('desired')
contactRF.name = "RF"

contactRF.support = ((0.11,-0.08,-0.08,0.11),(-0.045,-0.045,0.07,0.07),(-0.105,-0.105,-0.105,-0.105))
contactLF.support = ((0.11,-0.08,-0.08,0.11),(-0.07,-0.07,0.045,0.045),(-0.105,-0.105,-0.105,-0.105))
contactLF.support =  ((0.03,-0.03,-0.03,0.03),(-0.015,-0.015,0.015,0.015),(-0.105,-0.105,-0.105,-0.105))

#--- ZMP ---------------------------------------------------------------------
# zmp = ZmpEstimator('zmp')
# zmp.declare(sot,dyn)

#-----------------------------------------------------------------------------
# --- TRACE ------------------------------------------------------------------
#-----------------------------------------------------------------------------

from dynamic_graph.tracer import *
tr = Tracer('tr')
tr.open('/tmp/','planche_','.dat')

tr.add('dyn.com','com')
tr.add(taskCom.feature.name+'.error','ecom')
tr.add('dyn.waist','waist')
tr.add('dyn.rh','rh')
# tr.add('zmp.zmp','')
tr.add('dyn.position','')
tr.add('dyn.velocity','')
tr.add('robot.acceleration','robot_acceleration')
tr.add('robot.control','')
tr.add(taskCom.gain.name+'.gain','com_gain')
tr.add(taskrf.gain.name+'.gain','rf_gain')

tr.add('dyn.lf','lf')
tr.add('dyn.rf','rf')

tr.start()
robot.after.addSignal('tr.triger')
robot.after.addSignal(contactLF.task.name+'.error')
robot.after.addSignal('dyn.rf')
robot.after.addSignal('dyn.lf')
robot.after.addSignal('dyn.com')
robot.after.addSignal('sot.forcesNormal')
robot.after.addSignal('dyn.waist')

robot.after.addSignal('taskLim.normalizedPosition')
tr.add('taskLim.normalizedPosition','qn')

# history = History(dyn,1,zmp.zmp)

#-----------------------------------------------------------------------------
# --- RUN --------------------------------------------------------------------
#-----------------------------------------------------------------------------

DEG = 180.0/pi

# Angles for both knee, plus angle for the chest wrt the world.
MAX_EXT = 5/DEG
MAX_SUPPORT_EXT = 25/DEG
CHEST = 80/DEG # 80 ... 90?
WITH_FULL_EXTENTION=True
'''
MAX_EXT = 5/DEG
MAX_SUPPORT_EXT = 25/DEG
CHEST = 70/DEG # 80 ... 90?
WITH_FULL_EXTENTION=False
'''

'''
MAX_EXT = 45/DEG
MAX_SUPPORT_EXT = 45/DEG
CHEST = 50/DEG # 80 ... 90?
WITH_FULL_EXTENTION=False
'''

sot.clear()
contact(contactLF)
contact(contactRF)

taskCom.feature.selec.value = "11"
taskCom.gain.setByPoint(100,10,0.005,0.8)

taskrf.feature.frame('desired')
taskrf.gain.setByPoint(40,2,0.002,0.8)

taskChest.feature.selec.value='111000'
taskChest.ref = rotate('y',CHEST)
taskChest.gain.setByPoint(30,3,1/DEG,0.8)

taskPosture.gain.setByPoint(30,3,1/DEG,0.8)

ql = matrix(dyn.lowerJl.value)
ql[0,15] = MAX_SUPPORT_EXT
taskLim.referencePosInf.value = vectorToTuple(ql)

#sot.push(taskLim.name)
plug(robot.state,sot.position)

q0 = robot.state.value
rf0 = matrix(taskrf.feature.position.value)[0:3,3]



MetaTaskDynPosture.postureRange = postureRange[robotName]

# --- Events ---------------------------------------------
sigset = ( lambda s,v : s.__class__.value.__set__(s,v) )
refset = ( lambda mt,v : mt.__class__.ref.__set__(mt,v) )

attime(2
       ,(lambda : sot.push(taskCom.task.name),"Add COM")
       ,(lambda : refset(taskCom, ( 0.01, 0.09,  0.7 )), "Com to left foot")
       )

attime(140
       ,(lambda: sot.rmContact("RF"),"Remove RF contact" )
       ,(lambda: sot.push(taskrf.task.name), "Add RF")
       ,(lambda: gotoNd(taskrf, (0,0,0.65),"000110" ), "Up foot RF")
       )

# Was -.8,0,.8 with full extension
attime(500,lambda: gotoNd(taskrf, (-0.55,0,0.7),"000101" ), "Extend RF")

attime(800,lambda: sot.push(taskChest.task.name), "add chest")

attime(1000
       ,(lambda: sot.rm(taskrf.task.name), "rm RF")
       ,(lambda: sot.push(taskPosture.task.name), "add posture")
       ,(lambda: taskPosture.gotoq(chest=(0,),rleg=(0,0,0,MAX_EXT,0,0),head=(0,0,0,0)), "extend body")
       )

if WITH_FULL_EXTENTION:
    attime(1250
           ,lambda: taskPosture.gotoq(chest=(0,),rleg=(0,0,0,MAX_EXT,0,0),head=(0,0,0,0),rarm=(0,-pi/2,0,0,0,0,0),larm=(0,pi/2,0,0,0,0,0)), "extend arm")

    attime(2080
           ,lambda: taskPosture.gotoq(chest=(0,),rleg=(0,0,0,MAX_EXT,0.73,0),head=(0,-pi/4,0,0),rarm=(0,-pi/2,0,0,0,0,0),larm=(0,pi/2,0,0,0,0,0)), "extend foot")
    tex=1000
else: tex=0

rangeRL = postureRange[robotName]['rleg']
qRL0 = q0[min(rangeRL):max(rangeRL)+1]
rangeRA = postureRange[robotName]['rarm']
qRA0 = q0[min(rangeRA):max(rangeRA)+1]
rangeLA = postureRange[robotName]['larm']
qLA0 = q0[min(rangeLA):max(rangeLA)+1]

attime(1500 + tex
        ,(lambda: sot.rm(taskChest.task.name),"rm chest")
        ,(lambda: taskPosture.gotoq((30,3,1/DEG,0.8),chest=(0,),rleg=qRL0,head=(0,0,0,0),rarm=qRA0,larm=qLA0),"fold arms&leg")
        )

attime(1800+tex
       ,(lambda: sot.rm(taskPosture.task.name),"Remove posture" )
       ,(lambda: sot.push(taskrf.task.name), "Add RF")
       ,(lambda: gotoNd(taskrf, (-0.1,-0.1,0.25),"111" ), "Back RF")
       )

attime(2200+tex  ,lambda: goto6d(taskrf,vectorToTuple(rf0.T+(0,0,0.07)),(80,15,0.005,0.8))  , "RF to upper ground"       )
attime(2400+tex  ,lambda: goto6d(taskrf,vectorToTuple(rf0),(100,15,0.005,0.8))  , "RF to ground"       )
attime(2550+tex  
       ,(lambda: refset(taskCom,(0.01,0,0.65))  , "COM to zero"       )
       ,(lambda: taskCom.gain.setConstant(3)  , "lower com gain"       )
)
attime(2650+tex, lambda: sigset(sot.posture,q0), "Robot to initial pose")
attime(2650+tex  ,(lambda: contact(contactRF)  , "RF to contact"       )
       ,(lambda: sigset(taskCom.feature.selec,"111")  , "COM XYZ"       )
       ,(lambda: taskCom.gain.setByPoint(100,10,0.005,0.8)  , "upper com gain"       )
       )

attime(3200+tex,stop)

go()




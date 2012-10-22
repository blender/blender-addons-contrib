#!/usr/bin/python3
# To change this template, choose Tools | Templates
# and open the template in the editor.
#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****

bl_info = {
    "name": "Import: Sound to Animation",
    "author": "Vlassius",
    "version": (0, 50),
    "blender": (2, 57, 0),
    "api": 37023,
    "location": "Select a object -> go to the Object tab ->  Import Movement From Wav File",
    "description": "Extract movement from sound file. See the Object Panel at the end.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Import-Export/Import_Movement_From_Audio_File",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=23565&group_id=153&atid=467",
    "category": "Import-Export"}

"""
-- Extract movement from sound file, to help in animation - import script --<br> 

- NOTES:
- This script takes a wav file and get sound "movement" to help you in sync the movement to words in the wave file. <br>
- Supported Audio: .wav (wave) 8 bits and 16 bits <br>
- At least Blender 2.5.7 is necessary to run this program.

-v 0.50Beta- 
    Included: Auto Adjust Audio Sensity option    
    Included: 8 bits .wav file support
    Recalibrated: Manual audio sense 1    
    Cosmetic: Many changes in panel and terminal window info
    Corrected: Tracker_url
    Corrected: a few bytes in Memory Leaks
    work around: memory leak in function: bpy.ops.transform.rotate
    work around: memory leak in function: bpy.ops.anim.keyframe_insert
    
-v 0.22Beta- 
    Included: 
    Camera Rotation
    Empty Location-Rotation-Scale
    

-v 0.21Beta- 
    Changed just the meta informations like version and wiki page.
    

-v 0.20 Beta- 
    New Panel
    
    
-v 0.1.5 Beta- 
    Change in API-> Properties
    Included the button "Get FPS from Scene" due to a problem to get it in the start 
    Return to Frame 1 after import
    Filter .wav type file (by batFINGER)
    
-v 0.1.4 Beta- 
    If choose negative in rotation, auto check the rotation negative to Bones
    change in register()  unregister():

-v 0.1.3 Beta- 
    File Cleanup
    Change to bl_info. 
    Cosmetic Changes. 
    Minor change in API in how to define buttons. 
    Adjust in otimization.

-v 0.1.2 Beta
change in API- Update function bpy.ops.anim.keyframe_insert_menu 

-v 0.1.1 Beta
change in API- Update property of  window_manager.fileselect_add

-v 0.1.0 Beta
new - Added support to LAMP object         
new - improved flow to import
new - check the type of object before show options
bug - option max. and min. values
change- Updated scene properties for changes in property API.
        See http://lists.blender.org/pipermail/bf-committers/2010-September/028654.html

new flow:
          1) Process the sound file
          2) Show Button to import key frames 


- v0.0.4 ALPHA
new - Added destructive optimizer option - LostLestSignificativeDigit lost/total -> 10/255 default
new - Visual Graph to samples
new - Option to just process audio file and do not import - this is to help adjust the audio values
new - Get and show automatically the FPS (in proper field) information taking the information from scene
bug- Display sensitivity +1
bug - Corrected location of the script in description

- v0.0.3
Main change: Corrected to work INSIDE dir /install/linux2/2.53/scripts/addons
Corrected position of label "Rotation Negative"
Added correct way to deal with paths in Python os.path.join - os.path.normpath

- v0.0.2
Corrected initial error (Register() function)
Corrected some labels R. S. L.
Turned off "object field" for now
Changed target default to Z location 

- v0.0.1
Initial version



Credit to:
Vlassius

- http://vlassius.com.br
- vlassius@vlassius.com.br

"""

import bpy
from bpy.props import *
#from io_utils import ImportHelper
import wave

#TODO
#    Arrumar - não tem rotacao para objeto - so transformacao
#    alterar OBJETO NOMEADO

#    Colocar Escolha do Canal!!
#
#
#   colocar CANCELAR com ESC
#
#



#para deixar array global 
def _Interna_Globals(BytesDadosTotProcess, context):
    global array
    
    array= bytearray(BytesDadosTotProcess)  # cria array  
    context.scene.imp_sound_to_anim.bArrayCriado=True


def wavimport(context):
    #================================================================================================== 
    # Insert Key Frame
    #================================================================================================== 
    
#    print("Inside Wave Import...")   
    
    iDivScala= int(context.scene.imp_sound_to_anim.action_escale)     #scala do valor do movimento. [se =1 - 0 a 255 ] [se=255 - 0,00000 a 1,00000] [se=1000 - 0 a 0.255]

    bNaoValorIgual=True
    if context.scene.imp_sound_to_anim.action_valor_igual: bNaoValorIgual= False    # não deixa repetir valores
    
    iStartFrame= int(context.scene.imp_sound_to_anim.frames_initial)

    iMaxValue= context.scene.imp_sound_to_anim.action_max_value
    iMinValue= context.scene.imp_sound_to_anim.action_min_value
    
    bEscala=bRotacao=bEixo=False   
    if context.scene.imp_sound_to_anim.import_type=='imp_t_Scale':
        bEscala=True;
        
    if context.scene.imp_sound_to_anim.import_type=='imp_t_Rotation':
        bRotacao=True;

    if context.scene.imp_sound_to_anim.import_type=='imp_t_Location':
        bEixo=True;

    # atencao, nao é boolean
    iEixoXneg= iEixoYneg= iEixoZneg=1
    # atencao, nao é boolean
    iRotationNeg=1
    # atencao, nao é boolean
    iEscalaYneg= iEscalaZneg= iEscalaXneg=1
    bEixoX=bEixoY=bEixoZ=bEscalaX=bEscalaY=bEscalaZ=bRotationX=bRotationY=bRotationZ=False 

    # LOCAL 1
    if context.scene.imp_sound_to_anim.import_where1== 'imp_w_x':
        bEixoX=True
        bEscalaX=True
        bRotationX=True
        
    if context.scene.imp_sound_to_anim.import_where1== 'imp_w_y':
        bEixoY=True
        bEscalaY=True
        bRotationY=True

    if context.scene.imp_sound_to_anim.import_where1== 'imp_w_z':
        bEixoZ=True
        bEscalaZ=True
        bRotationZ=True

    if context.scene.imp_sound_to_anim.import_where1== 'imp_w_-x':
        bEixoX=True
        bEscalaX=True
        bRotationX=True
        iEixoXneg=-1
        iEscalaXneg=-1
        iRotationNeg=-1

    if context.scene.imp_sound_to_anim.import_where1== 'imp_w_-y':
        bEixoY=True
        bEscalaY=True
        bRotationY=True
        iEixoYneg=-1
        iRotationNeg=-1
        iEscalaYneg=-1

    if context.scene.imp_sound_to_anim.import_where1== 'imp_w_-z':
        bEixoZ=True
        bEscalaZ=True
        bRotationZ=True
        iEixoZneg=-1
        iRotationNeg=-1
        iEscalaZneg=-1


    # LOCAL 2
    if context.scene.imp_sound_to_anim.import_where2== 'imp_w_x':
        bEixoX=True
        bEscalaX=True
        bRotationX=True
        
    if context.scene.imp_sound_to_anim.import_where2== 'imp_w_y':
        bEixoY=True
        bEscalaY=True
        bRotationY=True

    if context.scene.imp_sound_to_anim.import_where2== 'imp_w_z':
        bEixoZ=True
        bEscalaZ=True
        bRotationZ=True

    if context.scene.imp_sound_to_anim.import_where2== 'imp_w_-x':
        bEixoX=True
        bEscalaX=True
        bRotationX=True
        iEixoXneg=-1
        iEscalaXneg=-1
        iRotationNeg=-1

    if context.scene.imp_sound_to_anim.import_where2== 'imp_w_-y':
        bEixoY=True
        bEscalaY=True
        bRotationY=True
        iEixoYneg=-1
        iRotationNeg=-1
        iEscalaYneg=-1

    if context.scene.imp_sound_to_anim.import_where2== 'imp_w_-z':
        bEixoZ=True
        bEscalaZ=True
        bRotationZ=True
        iEixoZneg=-1
        iRotationNeg=-1
        iEscalaZneg=-1


    # LOCAL 3
    if context.scene.imp_sound_to_anim.import_where3== 'imp_w_x':
        bEixoX=True
        bEscalaX=True
        bRotationX=True
        
    if context.scene.imp_sound_to_anim.import_where3== 'imp_w_y':
        bEixoY=True
        bEscalaY=True
        bRotationY=True

    if context.scene.imp_sound_to_anim.import_where3== 'imp_w_z':
        bEixoZ=True
        bEscalaZ=True
        bRotationZ=True

    if context.scene.imp_sound_to_anim.import_where3== 'imp_w_-x':
        bEixoX=True
        bEscalaX=True
        bRotationX=True
        iEixoXneg=-1
        iEscalaXneg=-1
        iRotationNeg=-1

    if context.scene.imp_sound_to_anim.import_where3== 'imp_w_-y':
        bEixoY=True
        bEscalaY=True
        bRotationY=True
        iEixoYneg=-1
        iRotationNeg=-1
        iEscalaYneg=-1

    if context.scene.imp_sound_to_anim.import_where3== 'imp_w_-z':
        bEixoZ=True
        bEscalaZ=True
        bRotationZ=True
        iEixoZneg=-1
        iRotationNeg=-1
        iEscalaZneg=-1

    iMinBaseX=iMinScaleBaseX=context.scene.imp_sound_to_anim.action_offset_x
    iMinBaseY=iMinScaleBaseY=context.scene.imp_sound_to_anim.action_offset_y
    iMinBaseZ=iMinScaleBaseZ=context.scene.imp_sound_to_anim.action_offset_z

    #escala inicia com 1 e não com zero
    iRotationAxisBaseX=context.scene.imp_sound_to_anim.action_offset_x  +1
    iRotationAxisBaseY=context.scene.imp_sound_to_anim.action_offset_y  +1
    iRotationAxisBaseZ=context.scene.imp_sound_to_anim.action_offset_z  +1

    #Added destructive optimizer option - LostLestSignificativeDigit lost/total
    iDestructiveOptimizer=context.scene.imp_sound_to_anim.optimization_destructive

    bLimitValue=False    #limita ou nao o valor - velocidade        

    if iMinValue<0: iMinValue=0
    if iMaxValue>255: iMaxValue=255
    if iMinValue>255: iMinValue=255
    if iMaxValue<0: iMaxValue=0    
    if iMinValue!= 0: bLimitValue= True
    if iMaxValue!= 255: bLimitValue= True


    print('')
    print("================================================================")   
    from time import strftime
    print(strftime("Start Import:  %H:%M:%S"))
    print("================================================================")   
    print('')

    ilocationXAnt=0
    ilocationYAnt=0
    ilocationZAnt=0
    iscaleXAnt=0
    iscaleYAnt=0
    iscaleZAnt=0
    iRotateValAnt=0
    iSumOptimizerP1=0
    iSumOptimizerP2=0
    iSumOptimizerP3=0
    iSumImportFrames=0

    # variavel global _Interna_Globals
    if context.scene.imp_sound_to_anim.bArrayCriado:
        for i in range(len(array)):

            #print(array[i])
            
            ival=array[i]/iDivScala
            #valor pequeno demais, vai dar zero na hora de aplicar
            if ival < 0.001: 
                 array[i]=0
                 ival=0
                 #print ("Valor Pequeno Demais, Zerando")
               
            # opcao de NAO colocar valores iguais sequenciais
            if i>0 and bNaoValorIgual and array[i-1]== array[i]:
                print("Importing Blender Frame: "+str(i)+"\tof "+str(len(array)-1) + "\t(skipped by optimizer)")
                iSumOptimizerP3+=1
                
            else:                 

                # otimizacao - não preciso mais que 2 valores iguais. pular key frame intermediario - Ex b, a, -, -, -, a
                # tambem otimiza pelo otimizador com perda
                if i>0 and i< len(array)-1 and abs(array[i] - array[i-1])<=iDestructiveOptimizer and abs(array[i] - array[i+1])<=iDestructiveOptimizer:# valor atual == anterior e posterior -> pula 
                        print("Importing Blender Frame: "+str(i)+"\tof "+str(len(array)-1) + "\t(skipped by optimizer)")
                        if iDestructiveOptimizer>0 and array[i] != array[i-1] or array[i] != array[i+1]: 
                            iSumOptimizerP1+=1
                            #print(array[i], iSumOptimizerP1) 
                        else: iSumOptimizerP2+=1
                else:           
                        if bLimitValue:
                            if array[i] > iMaxValue: array[i]=iMaxValue
                            if array[i] < iMinValue: array[i]=iMinValue

                        ival=array[i]/iDivScala
                        #print("teste ival= " + str(ival))    ####
                        #passa para float com somente 3 digitos caso seja float
                        m_ival=ival*1000
                        if int(m_ival) != m_ival:
                            ival= int(m_ival)
                            ival = ival /1000
                            #print("Novo ival= " + str(ival))    ####

                        bpy.context.scene.frame_current = i+iStartFrame

                        if bpy.context.active_object.type=='MESH' or bpy.context.active_object.type=='CAMERA' or bpy.context.active_object.type=='EMPTY':   #precisa fazer objeto ativo
                            if bEixo:                   
                                if bEixoX: bpy.context.active_object.location.x = ival*iEixoXneg+iMinBaseX
                                if bEixoY: bpy.context.active_object.location.y = ival*iEixoYneg+iMinBaseY
                                if bEixoZ: bpy.context.active_object.location.z = ival*iEixoZneg+iMinBaseZ               
                                #print("mesh ou camera em eixo")  ####
                            
                            if bEscala:
                                if bEscalaX: bpy.context.active_object.scale.x = ival*iEscalaXneg+iMinScaleBaseX
                                if bEscalaY: bpy.context.active_object.scale.y = ival*iEscalaYneg+iMinScaleBaseY
                                if bEscalaZ: bpy.context.active_object.scale.z = ival*iEscalaZneg+iMinScaleBaseZ 

                        # 'ARMATURE' or ('MESH' and bRotacao) or ('CAMERA' and bRotacao) or 'LAMP' or 'EMPTY' and bRotacao)
                        if bpy.context.active_object.type=='ARMATURE' or (bpy.context.active_object.type=='MESH' and bRotacao) or (bpy.context.active_object.type=='CAMERA' and bRotacao) or bpy.context.active_object.type=='LAMP' or (bpy.context.active_object.type=='EMPTY' and bRotacao):

                                ###############  BONE ######################
                                if bpy.context.active_object.type=='ARMATURE':   #precisa ser objeto ativo. Nao achei como passar para editmode
                                    if bpy.context.mode!= 'POSE':    #posemode 
                                        bpy.ops.object.posemode_toggle()
                                        #print("bone pose mode")   ####
    
                                ###############  ALL ######################    
                                if bEixo:
                                    if ilocationXAnt!=0 or ilocationYAnt!=0 or ilocationZAnt!=0: 
                                        bpy.ops.transform.translate(value=(ilocationXAnt*-1, ilocationYAnt*-1, ilocationZAnt*-1), constraint_axis=(bEixoX, bEixoY,bEixoZ), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)  
                                    
                                    ilocationX=ilocationY=ilocationZ=0                
                                    if bEixoX: ilocationX = ival*iEixoXneg+iMinBaseX
                                    if bEixoY: ilocationY = ival*iEixoYneg+iMinBaseY
                                    if bEixoZ: ilocationZ = ival*iEixoZneg+iMinBaseZ  
                                    bpy.ops.transform.translate(value=(ilocationX, ilocationY, ilocationZ), constraint_axis=(bEixoX, bEixoY,bEixoZ), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)
                                    ilocationXAnt= ilocationX
                                    ilocationYAnt= ilocationY
                                    ilocationZAnt= ilocationZ 
            
                                if bEscala:
                                    if iscaleXAnt!=0 or iscaleYAnt!=0 or iscaleZAnt!=0:
                                        tmpscaleXAnt=0
                                        tmpscaleYAnt=0
                                        tmpscaleZAnt=0
                                        if iscaleXAnt: tmpscaleXAnt=1/iscaleXAnt
                                        if iscaleYAnt: tmpscaleYAnt=1/iscaleYAnt
                                        if iscaleZAnt: tmpscaleZAnt=1/iscaleZAnt 
                                        bpy.ops.transform.resize(value=(tmpscaleXAnt, tmpscaleYAnt, tmpscaleZAnt ), constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)  
                                    
                                    iscaleX=iscaleY=iscaleZ=0                
                                    if bEscalaX: iscaleX = ival*iEscalaXneg+iMinScaleBaseX
                                    if bEscalaY: iscaleY = ival*iEscalaYneg+iMinScaleBaseY
                                    if bEscalaZ: iscaleZ = ival*iEscalaZneg+iMinScaleBaseZ                        
                                    bpy.ops.transform.resize(value=(iscaleX, iscaleY, iscaleZ), constraint_axis=(False, False, False), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)
                                    iscaleXAnt= iscaleX
                                    iscaleYAnt= iscaleY
                                    iscaleZAnt= iscaleZ                       
                                    
                                if bRotacao:                        
                                    if iRotateValAnt!=0: 
                                        # memory leak
                                        #bpy.ops.transform.rotate(value= (iRotateValAnt*-1), axis=(iRotationAxisBaseX, iRotationAxisBaseY, iRotationAxisBaseZ), constraint_axis=(bRotationX, bRotationY, bRotationZ), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)                                                                   
                                        bpy.context.active_object.rotation_euler= ((iRotateValAnt*-1)+iRotationAxisBaseX)*bRotationX , ((iRotateValAnt*-1)+iRotationAxisBaseY)*bRotationY , ((iRotateValAnt*-1)+iRotationAxisBaseZ)*bRotationZ 
                                        
                                    #memory leak    
                                    #bpy.ops.transform.rotate(value= (ival*iRotationNeg), axis=(iRotationAxisBaseX, iRotationAxisBaseY, iRotationAxisBaseZ), constraint_axis=(bRotationX, bRotationY, bRotationZ), constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False, snap_target='CLOSEST', snap_point=(0, 0, 0), snap_align=False, snap_normal=(0, 0, 0), release_confirm=False)
                                    bpy.context.active_object.rotation_euler= ((ival*iRotationNeg)+ iRotationAxisBaseX)* bRotationX, ((ival*iRotationNeg)+ iRotationAxisBaseY)* bRotationY, ((ival*iRotationNeg)+ iRotationAxisBaseZ)* bRotationZ
                                    iRotateValAnt= ival*iRotationNeg
                       
                        ob = bpy.context.active_object
                    
                        if bEixo:
                            ob.keyframe_insert(data_path="location")                          
                                                        
                        if bRotacao:
                            ob.keyframe_insert(data_path="rotation_euler")                            
                            
                        if bEscala:
                            ob.keyframe_insert(data_path="scale")
                    
                    
                        #   *** Problem Memory Leak ***
                        #if bEixo and not bEscala and not bRotacao:
                        #    bpy.ops.anim.keyframe_insert(type='Location')                 
                                                        
                        #if bRotacao and not bEixo and not bEscala:
                        #    bpy.ops.anim.keyframe_insert(type='Rotation')
                            
                        #if bEscala and not bEixo and not bRotacao:
                        #   bpy.ops.anim.keyframe_insert(type='Scaling')
            
                        #if bEixo and bRotacao:
                        #    bpy.ops.anim.keyframe_insert(type='LocRot')
                           
                        #if bEscala and bEixo:
                        #    bpy.ops.anim.keyframe_insert(type='LocScale')
            
                        #if bEixo and bRotacao and bEscala:
                        #    bpy.ops.anim.keyframe_insert(type='LocRotScale')
            
                        #if bEscala and bRotacao:
                        #    bpy.ops.anim.keyframe_insert(type='RotScale')
                                     
                    
                        print("Importing Blender Frame: "+str(i)+"\tof "+str(len(array)-1) + "\tValue: "+ str(ival))
#                        context.scene.imp_sound_to_anim.Info_Import= "Importing Frame: "+str(i)+" of "+str(len(array)-1)
#                        bpy.context.scene.imp_sound_to_anim.update()   

                        iSumImportFrames+=1
                        
                # FIm do ELSE otimizador 
            # Fim bNaoValorIgual

    bpy.context.scene.frame_current = 1

    context.scene.imp_sound_to_anim.Info_Import="Done. Imported " + str(iSumImportFrames) + " Frames" 
#    context.scene.imp_sound_to_anim.bArrayCriado=False   # nao precisa importar novamente sem processar audio novamente
    
    print('')
    print("================================================================")
    print("Imported: " +str(iSumImportFrames) + " Key Frames")
    print("Optimizer Pass 1 prepared to optimize: " +str(iSumOptimizerP1) + " blocks of Frames")
    print("Optimizer Pass 2 has optimized: " +str(iSumOptimizerP2) + " Frames")
    print("Optimizer Pass 3 has optimized: " +str(iSumOptimizerP3) + " Frames")
    print("Optimizer has optimized: " +str(iSumOptimizerP1 + iSumOptimizerP2+iSumOptimizerP3) + " Frames")       
    print(strftime("End Import:  %H:%M:%S - by Vlassius"))
    print("================================================================")   
    print('')
   
    
#================================================================================================== 
# Sound Converter
#================================================================================================== 

def SoundConv(File, DivSens, Sensibil, Resol, context, bAutoSense):

    try:
        Wave_read= wave.open(File, 'rb')
    except IOError as e:
        print("File Open Error: ", e)
        return False

    NumCh=      Wave_read.getnchannels()
    SampW=      Wave_read.getsampwidth() // NumCh # 8, 16, 24 32 bits
    FrameR=     Wave_read.getframerate() // NumCh
    NumFr=      Wave_read.getnframes()
    ChkCompr=   Wave_read.getcomptype()
    
    if ChkCompr != "NONE":
        print('Sorry, this compressed Format is NOT Supported ', ChkCompr)
        context.scene.imp_sound_to_anim.Info_Import= "Sorry, this compressed Format is NOT Supported " 
        return False
    
    if SampW > 2:
        context.scene.imp_sound_to_anim.Info_Import= "Sorry, supported .wav files 8 and 16 bits only" 
        print('Sorry, supported .wav files 8 and 16 bits only')
        return False

    context.scene.imp_sound_to_anim.Info_Import=""
    
    # usado para achar contorno da onda - achando picos 
    # numero de audio frames para cada video frame
    BytesResol= int(FrameR/Resol)
    
    # com 8 bits/S - razao Sample/s por resolucao
    # tamanho do array
    BytesDadosTotProcess= NumFr // BytesResol 

    # inicia array
    _Interna_Globals(BytesDadosTotProcess, context)
    
    print('')
    print("================================================================")   
    from time import strftime
    print(strftime("Go!  %H:%M:%S"))
    print("================================================================")   
    print('')   
    print('Total Audio Time: \t ' + str(NumFr//FrameR) + 's (' + str(NumFr//FrameR//60) + 'min)')
    print('Total # Interactions: \t', BytesDadosTotProcess)
    print('Total Audio Frames: \t', NumFr)
    print('Frames/s: \t\t ' + str(FrameR))
    print('# Chanels in File: \t', NumCh)
    print('Channel in use:\t\t 1')
    print('Bit/Sample/Chanel: \t ' + str(SampW*8))
    print('# Frames/Act: \t\t', DivSens)
    
    if bAutoSense==0:
        print('Audio Sensitivity: \t', Sensibil+1)
    else:
        print('Using Auto Audio Sentivity. This is pass 1 of 2.')
        Sensibil=0  # if auto sense, Sensibil must be zero here
        arrayAutoSense= bytearray((BytesDadosTotProcess)*2)  # cria array para AutoAudioSense         
        MaxAudio=0; # valor maximo de audio encontrado
    print(' ')


#    _array= bytearray(BytesDadosTotProcess)  # cria array
    j=0  # usado de indice
    
    print ("Sample->[value]\tAudio Frame #   \t\t[Graph Value]")

    # laço total leitura bytes
    # armazena dado de pico
    looptot= int(BytesDadosTotProcess // DivSens)    
    for jj in range(looptot):      
        
        # caso de 2 canais (esterio)
        # uso apenas 2 bytes em 16 bits, ie, apenas canal esquerdo
        # [0] e [1] para CH L
        # [2] e [3] para CH R      
        # uso 1 byte se em 8 bits
        ValorPico=0
        for i in range(BytesResol):    # leio o numero de frames de audio para cada frame de video, valor em torno de 1000
            frame = Wave_read.readframes(DivSens) #loop exterior copia DivSens frames a cada frame calculado
            if len(frame)==0: break

            if bAutoSense==0:    # AutoAudioSense Desligado

                if SampW ==1:
                    if frame[0]> ValorPico: 
                        ValorPico= frame[0]               

                if SampW ==2:                # frame[0] baixa       frame[1] ALTA BIT 1 TEM SINAL
                    if Sensibil ==0:
                        if frame[1] <127:    # se bit1 =0, usa o valor - se bit1=1 quer dizer numero negativo
                            if frame[1] > ValorPico: 
                                ValorPico= frame[1]               
                            
                    elif Sensibil ==4:
                        if frame[1] < 127:     # se bit1 =0, usa o valor
                            frame0= ((frame[0] & 0b11111100) >> 2) | ((frame[1] & 0b00000011) << 6)                        
                            if frame0 > ValorPico: 
                                    ValorPico= frame0               

                    elif Sensibil ==3:
                        if frame[1] < 127:    # se bit1 =0, usa o valor
                            frame0= ((frame[0] & 0b11110000) >> 4) | ((frame[1] & 0b00001111) << 4)                        
                            if frame0 > ValorPico: 
                                    ValorPico= frame0               

                    elif Sensibil ==2:
                        if frame[1] < 127:    # se bit1 =0, usa o valor
                            frame0= ((frame[0] & 0b11100000) >> 5) | ((frame[1] & 0b00011111) << 3)                        
                            if frame0 > ValorPico: 
                                    ValorPico= frame0               

                    elif Sensibil ==1:
                        if frame[1] < 127:    # se bit1 =0, usa o valor
                            frame0= ((frame[0] & 0b11000000) >> 6) | ((frame[1] & 0b00111111) << 2)                        
                            if frame0 > ValorPico: 
                                    ValorPico= frame0               

                    elif Sensibil ==5:
                        if frame[0] > ValorPico: 
                            ValorPico= frame[0]    

            else:   # AutoAudioSense Ligado
                if SampW ==1:
                    if frame[0]> MaxAudio:                         
                        MaxAudio = frame[0] 
                        
                    if frame[0]> ValorPico: 
                        ValorPico=frame[0]
                
                if SampW ==2:   
                    if frame[1] < 127:
                        tmpValorPico= frame[1] << 8
                        tmpValorPico+=  frame[0]
                        
                        if tmpValorPico > MaxAudio:
                            MaxAudio = tmpValorPico 
                            
                        if tmpValorPico > ValorPico:
                            ValorPico= tmpValorPico
                

        if bAutoSense==0:    #autoaudiosense desligado
            # repito o valor de frames por actions (OTIMIZAR)
            for ii in range(DivSens):           
                array[j]=ValorPico  # valor de pico encontrado
                j +=1           # incrementa indice prox local
        else:
            
            arrayAutoSense[j]= (ValorPico & 0b0000000011111111) #copia valores baixos
            arrayAutoSense[j+1]= (ValorPico & 0b1111111100000000) >> 8   #copia valores altos
            j+=2
            
            #print("baixo=" + str(arrayAutoSense[j-2]) + "  alto= " + str(arrayAutoSense[j-1]))

        if bAutoSense==0:    #autoaudiosense desligado
            igraph= ValorPico//10
        else:
            if SampW ==2:
                igraph= ValorPico//1261
            
            else:
                igraph= ValorPico//10    
        
        stgraph="["        
        for iii in range(igraph): 
            stgraph+="+" 
       
        for iiii in range(26-igraph): 
            stgraph+=" " 
        stgraph+="]"
        
        print ("Sample-> " + str(ValorPico) + "\tAudio Frame #  " + str(jj) + " of " + str(looptot-1) + "\t"+ stgraph)
                        
        #print (str(MaxAudio))


    if bAutoSense==1:
        print(".")   
        print("================================================================")           
        print('Calculating Auto Audio Sentivity, pass 2 of 2.')
        print("================================================================")           
        print(".")           
        
        # para transformar 15 bits em 8 calibrando valor maximo -> fazer regra de 3
        # MaxAudio -> 255
        # outros valores => valor calibrado= (255 * Valor) / MaxAudio    

        # passar do arrayAutoSense[] para array[]
        # reimprimir grafico 

        scale= 255/MaxAudio
        
        j=0
        jj=0
        print ("Sample->[value]\tAudio Frame #    \t\t[Graph Value]")    
        
        for i in range(BytesDadosTotProcess // DivSens): 
            
            ValorOriginal= arrayAutoSense[j+1] << 8
            ValorOriginal+= arrayAutoSense[j]
            ValorOriginal= ((round(ValorOriginal * scale)) & 0b11111111)
                       
            for ii in range(DivSens):
                array[jj] = ValorOriginal
                jj += 1   # se autoaudiosense, o array tem dois bytes para cada valor

            j+=2            
            #print(" baixo=" + str(arrayAutoSense[j-2]) + "  alto= " + str(arrayAutoSense[j-1]) + " junto= " + str(ValorOriginal) + " array= " + str(array[jj-1]))            
            
            igraph= round(array[jj-1]/10)
            
            stgraph="["        
            for iii in range(igraph): 
                stgraph+="+" 
           
            for iiii in range(26-igraph): 
                stgraph+=" " 
            stgraph+="]"
            print ("Sample-> " + str(array[jj-1]) + "\tAudio Frame #  " + str(i) + " of " + str(looptot-1) + "\t"+ stgraph)    
            
        #limpa array tmp
        del arrayAutoSense[:]

# fim
#    print(_array)
    context.scene.imp_sound_to_anim.Info_Import= "Click \"Import Key frames\" to begin import" #this set the initial text

    print("================================================================")   
    print(strftime("End Process:  %H:%M:%S"))
    print("================================================================")   

    try:
        Wave_read.close()
    except:
        print('File Close Error')
        
    return

#
#
#================================================================================================== 
#================================================================================================== 
#================================================================================================== 
#
#
# BLENDER Configuration - Blender Beta
#
#
#================================================================================================== 
#================================================================================================== 
#================================================================================================== 
#    
#

class VIEW3D_PT_CustomMenuPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "Import Movement From Wav File"
    bl_options = {'DEFAULT_CLOSED'}   

    def draw(self, context):
        layout = self.layout

        b=bpy.context.active_object.type=='EMPTY' or bpy.context.active_object.type=='ARMATURE' or bpy.context.active_object.type=='MESH' or bpy.context.active_object.type=='CAMERA' or bpy.context.active_object.type=='LAMP' 
        if not b:
            row=layout.row()
            row.label(text="The Selected Object is: type \"" + bpy.context.active_object.type + "\", and it is not supported.") 
            row=layout.row()
            row.label(text="Supported Object are Type: Armature, Mesh, Camera and Lamp") 
            row=layout.row()
        else:

            #print(context.scene.imp_sound_to_anim.bTypeImport)
    
            if context.scene.imp_sound_to_anim.bTypeImport == 0:
                #To use Direct 
                #mount panel to Direct animation 
                row=layout.row()
                layout.operator("import.sound_animation_botao_udirect")           


            #-----------------------------
            #Direct Animation
            #-----------------------------
            if context.scene.imp_sound_to_anim.bTypeImport == 1:
                row=layout.row()
                row.label(text="With Object Selected,") 
                row=layout.row()
                row.label(text="1)Click button \"Process Wav\",")
                row=layout.row()
                row.label(text="(Check the Terminal Window)")
                row=layout.row()
                row.label(text="2)Click Button \"Import Key Frames\",")
                row=layout.row()        
                row.label(text="Run the animation (alt A) and Enjoy!")        
                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"action_auto_audio_sense")
                row=layout.row()        
                if context.scene.imp_sound_to_anim.action_auto_audio_sense == 0:   # se auto audio sense desligado
                    row.prop(context.scene.imp_sound_to_anim,"audio_sense")
                    row=layout.row()                
                row.prop(context.scene.imp_sound_to_anim,"action_per_second")
                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"action_escale")
    
                #row=layout.row()
                row.label(text="Result from 0 to " + str(   round(255/context.scene.imp_sound_to_anim.action_escale,4)  ) + "")
                
                row=layout.row()
                row.label(text="Property to Change:")
                row.prop(context.scene.imp_sound_to_anim,"import_type")

                #coluna
                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"import_where1")
                row.prop(context.scene.imp_sound_to_anim,"import_where2")
                row.prop(context.scene.imp_sound_to_anim,"import_where3")

                row=layout.row()   
                row.label(text='Optional Configurations:')
                row=layout.row()   
                
                row.prop(context.scene.imp_sound_to_anim,"frames_per_second")
                row=layout.row()     
                #coluna
                column= layout.column()
                split=column.split(percentage=0.5)
                col=split.column()

                row=col.row()
                row.prop(context.scene.imp_sound_to_anim,"frames_initial")
                
                row=col.row()
                row.prop(context.scene.imp_sound_to_anim,"action_min_value")

                col=split.column()          

                row=col.row()
                row.prop(context.scene.imp_sound_to_anim,"optimization_destructive")               

                row=col.row()
                row.prop(context.scene.imp_sound_to_anim,"action_max_value")
                
                row=layout.row()
                
                row.prop(context.scene.imp_sound_to_anim,"action_offset_x")
                row.prop(context.scene.imp_sound_to_anim,"action_offset_y")
                row.prop(context.scene.imp_sound_to_anim,"action_offset_z")
                
                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"action_valor_igual")        
                
                #operator button
                #OBJECT_OT_Botao_Go => Botao_GO
                row=layout.row()
                layout.operator(OBJECT_OT_Botao_Go.bl_idname)
    
                row=layout.row()
                row.label(text=context.scene.imp_sound_to_anim.Info_Import)
                if context.scene.imp_sound_to_anim.bArrayCriado:                              
                    layout.operator(OBJECT_OT_Botao_Import.bl_idname)
                    row=layout.row()
    


    
            #-----------------------------
            #Use Driver
            #-----------------------------            
            if context.scene.imp_sound_to_anim.bTypeImport == 2:            

                row=layout.row()        
                row.prop(context.scene.imp_sound_to_anim,"audio_sense")
                row=layout.row()
                row.prop(context.scene.imp_sound_to_anim,"frames_per_second")
                row=layout.row()     
                row.prop(context.scene.imp_sound_to_anim,"action_per_second")

                row=layout.row()
                layout.operator(ImportWavFile.bl_idname)
            



class ImpSoundtoAnim(bpy.types.PropertyGroup):
    
                    
        bArrayCriado = IntProperty(name="", 
            description="Avisa que rodou process de som",
            default=0)
 
        #Nome do objeto
        Info_Import = StringProperty(name="",        
            description="Info about Import",
            maxlen= 1024,
            default= "")#this set the initial text
        
        #    iAudioSensib=0    #sensibilidade volume do audio 0 a 5. Quanto maior, mais sensibilidade
        audio_sense = IntProperty(name="Audio Sens",         
            description="Audio Sensibility.",
            min=1,
            max=6,
            step=1,
            default= 1)
        
        #    iFramesPorSeg=15  #Frames por segundo para key frame
        #fps= (bpy.types.Scene) bpy.context.scene.render.fps
        frames_per_second = IntProperty(name="#Frames/s",        
            description="Frames you want per second. Better match your set up in Blender scene.",
            min=1,
            max=120,
            step=1)    
              
        #    iMovPorSeg=1      #Sensibilidade de movimento. 3= 3 movimentos por segundo
        action_per_second = IntProperty(name="Act/s",        
            description="Actions per second. From 1 to #Frames/s",
            min=1,
            max=120,
            step=1,
            default= 4)#this set the initial text
        
        #    iDivScala=200     #scala do valor do movimento. [se =1 - 0 a 255 ] [se=255 - 0,00000 a 1,00000] [se=1000 - 0 a 0.255]
        action_escale = IntProperty(name="Scale",        
            description="Scale the result values. See the text at right side of the field",
            min=1,
            max=99999,
            step=100,                                    
            default= 100)#this set the initial text
        
        #    iMaxValue=255
        action_max_value = IntProperty(name="Clip Max",        
            description="Set the max value (clip higher values).",
            min=1,
            max=255,
            step=1,                                    
            default= 255)#this set the initial text
        
        #    iMinValue=0
        action_min_value = IntProperty(name="Clip Min",        
            description="Set the min value. (clip lower values)",
            min=0,
            max=255,
            step=1,                                    
            default= 0)#this set the initial text
        
        #    iStartFrame=0#
        frames_initial = IntProperty(name="Frame Ini",        
            description="Where to start to put the computed values.",
            min=0,
            max=999999999,
            step=1,                             
            default= 0)
        
        
        #########  ADICIONAIS ################
        
        action_offset_x = FloatProperty(name="XOffset",        
            description="Offset X Values",
            min=-999999,
            max=999999,
            step=1,                       
            default= 0)

        action_offset_y = FloatProperty(name="YOffset",
            description="Offset Y Values",
            min=-999999,
            max=999999,
            step=1,                       
            default= 0)

        action_offset_z = FloatProperty(name="ZOffset",
            description="Offset Z Values",
            min=-999999,
            max=999999,
            step=1,                       
            default= 0)


        import_type= EnumProperty(items=(('imp_t_Scale', "Scale", "Apply to Scale"),
                                         ('imp_t_Rotation', "Rotation", "Apply to Rotation"),
                                         ('imp_t_Location', "Location", "Apply to Location")                                                                                 
                                        ),
                                 name="",
                                 description= "Property to Import Values",
                                 default='imp_t_Location')

        import_where1= EnumProperty(items=(('imp_w_-z', "-z", "Apply to -z"),
                                          ('imp_w_-y', "-y", "Apply to -y"),
                                          ('imp_w_-x', "-x", "Apply to -x"),
                                          ('imp_w_z', "z", "Apply to z"),
                                          ('imp_w_y', "y", "Apply to y"),
                                          ('imp_w_x', "x", "Apply to x")
                                        ),
                                 name="",
                                 description= "Where to Import",
                                 default='imp_w_z')

        import_where2= EnumProperty(items=(('imp_w_none', "None", ""),
                                          ('imp_w_-z', "-z", "Apply to -z"),
                                          ('imp_w_-y', "-y", "Apply to -y"),
                                          ('imp_w_-x', "-x", "Apply to -x"),
                                          ('imp_w_z', "z", "Apply to z"),
                                          ('imp_w_y', "y", "Apply to y"),
                                          ('imp_w_x', "x", "Apply to x")
                                        ),
                                 name="",
                                 description= "Where to Import",
                                 default='imp_w_none')

        import_where3= EnumProperty(items=(('imp_w_none', "None", ""),
                                          ('imp_w_-z', "-z", "Apply to -z"),
                                          ('imp_w_-y', "-y", "Apply to -y"),
                                          ('imp_w_-x', "-x", "Apply to -x"),
                                          ('imp_w_z', "z", "Apply to z"),
                                          ('imp_w_y', "y", "Apply to y"),
                                          ('imp_w_x', "x", "Apply to x")
                                        ),
                                 name="",
                                 description= "Where to Import",
                                 default='imp_w_none')

        
        ############## Propriedades boolean  ###################

        #  INVERTIDO!!!  bNaoValorIgual=True    # não deixa repetir valores     INVERTIDO!!!   
        action_valor_igual = BoolProperty(name="Hard Transition",
            description="Use to movements like a mouth, to a arm movement, maybe you will not use this.",
            default=1)
        
        action_auto_audio_sense = BoolProperty(name="Auto Audio Sensitivity",
            description="Try to discover best audio scale. ",
            default=1)
        
        #
        #  Optimization
        #                 
        optimization_destructive = IntProperty(name="Optimization",        
            description="Hi value = Hi optimization -> Hi loss of information.",
            min=0,
            max=254,
            step=10,
            default= 10)

        # import as driver or direct
        # not defined
        # Direct=1
        # Driver=2
        bTypeImport = IntProperty(name="",        
            description="Import Direct or Driver",
            default=0)
        

           
from bpy.props import *

def WavFileImport(self, context):     
    self.layout.operator(ImportWavFile.bl_idname, text="Import a wav file", icon='PLUGIN') 




####################################################################################
#
#     USE DIRECT 
#
####################################################################################

class OBJECT_OT_Botao_uDirect(bpy.types.Operator):
    '''Import as Direct Animation'''
    bl_idname = "import.sound_animation_botao_udirect"
    bl_label = "Direct to a Property"

    def execute(self, context):
        context.scene.imp_sound_to_anim.bTypeImport= 1
        if context.scene.imp_sound_to_anim.frames_per_second == 0:
             context.scene.imp_sound_to_anim.frames_per_second= bpy.context.scene.render.fps
        return{'FINISHED'}    
    
    def invoke(self, context, event):
        self.execute(context)
        #return {'RUNNING_MODAL'}
        return {'FINISHED'}



####################################################################################
#
#     bptao iniciar process som
#
####################################################################################

class OBJECT_OT_Botao_Import(bpy.types.Operator):
    '''Import Key Frames to Blender'''
    bl_idname = "import.sound_animation_botao_import"
    bl_label = "Import Key Frames"

    def execute(self, context):
#        print("Running Wave Import...")
        #context.scene.imp_sound_to_anim.Info_Import= "Working. See the terminal window." #this set the initial text
        wavimport(context)
        return{'FINISHED'} 
      
    def invoke(self, context, event):
        self.execute(context)
        #return {'RUNNING_MODAL'}
        return {'FINISHED'}

####################################################################################
#
#     bptao iniciar process som
#
####################################################################################
class OBJECT_OT_Botao_Go(bpy.types.Operator):
    ''''''
    bl_idname = "import.sound_animation_botao_go"
    # change in API
    bl_description = "Process a .wav file, take movement from the sound and import to the scene as Key"
    bl_label = "Process Wav"

# change sugested batFINGER
    filter_glob = StringProperty(default="*.wav", options={'HIDDEN'})

    path = StringProperty(name="File Path", description="Filepath used for importing the WAV file", maxlen= 1024, default= "")

    filename = StringProperty(name="File Name",
                              description="Name of the file")
                              
    directory = StringProperty(name="Directory",
                               description="Directory of the file")

    def execute(self, context):   
        # nao funciona self.properties.path
#        print("File Selected: ", self.properties.path)#display the file name and current path
#        print("Filename: ", self.properties.filename)#display the file name and current path
#        print("Directory Selected: ", self.properties.directory)#display the file name and current path        
        import os 
        f= os.path.join(self.properties.directory, self.properties.filename)
        f= os.path.normpath(f)
                            
        print (" ")
        print (" ")
        print ("Selected file = ",f)
        checktype = f.split('\\')[-1].split('.')[1]
        if checktype.upper() != 'WAV':
            print ("ERROR!! Selected file = ", f)
            print ("ERROR!! Its not a .wav file")
            return

        iAudioSensib= int(context.scene.imp_sound_to_anim.audio_sense)-1    #sensibilidade volume do audio 0 a 5. Quanto maior, mais sensibilidade
        if iAudioSensib <0: iAudioSensib=0
        elif iAudioSensib>5: iAudioSensib=5
    
        if context.scene.imp_sound_to_anim.action_per_second > context.scene.imp_sound_to_anim.frames_per_second:   #act/s nao pode se maior que frames/s
            context.scene.imp_sound_to_anim.action_per_second = context.scene.imp_sound_to_anim.frames_per_second    
        
        iFramesPorSeg= int(context.scene.imp_sound_to_anim.frames_per_second)  #Frames por segundo para key frame
        
        iMovPorSeg= int(context.scene.imp_sound_to_anim.action_per_second)      #Sensibilidade de movimento. 3= 3 movimentos por segundo
       
        #iDivMovPorSeg Padrao - taxa 4/s ou a cada 0,25s  => iFramesPorSeg/iDivMovPorSeg= ~0.25
        for i in range(iFramesPorSeg):
            iDivMovPorSeg=iFramesPorSeg/(i+1)
            if iFramesPorSeg/iDivMovPorSeg >=iMovPorSeg:
                break    

        # chama funcao de converter som, retorna preenchendo _Interna_Globals.array
        SoundConv(f, int(iDivMovPorSeg), iAudioSensib, iFramesPorSeg, context, context.scene.imp_sound_to_anim.action_auto_audio_sense)
        return {'FINISHED'}

      
    def invoke(self, context, event):
        #need to set a path so so we can get the file name and path
        wm = context.window_manager
        wm.fileselect_add(self)

        return {'RUNNING_MODAL'}  


  
def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.imp_sound_to_anim = PointerProperty(type=ImpSoundtoAnim, name="Import: Sound to Animation", description="Extract movement from sound file. See the Object Panel at the end.")
    bpy.types.INFO_MT_file_import.append(WavFileImport) 


def unregister():
    print("*************Inside UNregister...**********")  
    
    try:
        bpy.utils.unregister_module(__name__)
    except:
        pass
        
    try:
        bpy.types.INFO_MT_file_import.remove(WavFileImport)
    except:
        pass



if __name__ == "__main__":
    register()
    

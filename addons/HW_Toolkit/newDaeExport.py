# Updated:
#  Converts all materials to phong on export
# Dom2 14-JUL-2019

import bpy
import math
import time
from mathutils import *

C = bpy.context
D = bpy.data

#############
#DAE Schemas#
#############

#Just defining all the DAE attributes here so the processing functions are more easily readable

#Utility Schemas
DAENode = "{http://www.collada.org/2005/11/COLLADASchema}node"
DAETranslation = "{http://www.collada.org/2005/11/COLLADASchema}translate"
DAEInit = "{http://www.collada.org/2005/11/COLLADASchema}init_from"
DAEInput = "{http://www.collada.org/2005/11/COLLADASchema}input"
DAEFloats = "{http://www.collada.org/2005/11/COLLADASchema}float_array"
DAESource = "{http://www.collada.org/2005/11/COLLADASchema}source"
DAEInstance = "{http://www.collada.org/2005/11/COLLADASchema}instance_geometry"

##Material Schemas
DAELibMaterials = "{http://www.collada.org/2005/11/COLLADASchema}library_materials"
DAEMaterials = "{http://www.collada.org/2005/11/COLLADASchema}material"
DAELibEffects = "{http://www.collada.org/2005/11/COLLADASchema}library_effects"
DAEfx = "{http://www.collada.org/2005/11/COLLADASchema}effect"
DAELibImages = "{http://www.collada.org/2005/11/COLLADASchema}library_images"
DAEimage = "{http://www.collada.org/2005/11/COLLADASchema}image"
DAETex = "{http://www.collada.org/2005/11/COLLADASchema}texture"
DAEProfile = "{http://www.collada.org/2005/11/COLLADASchema}profile_COMMON"
DAETechnique = "{http://www.collada.org/2005/11/COLLADASchema}technique"
DAEPhong = "{http://www.collada.org/2005/11/COLLADASchema}phong"

#Geometry Schemas
DAEGeo = "{http://www.collada.org/2005/11/COLLADASchema}geometry"
DAEMesh = "{http://www.collada.org/2005/11/COLLADASchema}mesh"
DAEVerts = "{http://www.collada.org/2005/11/COLLADASchema}vertices"
DAETris = "{http://www.collada.org/2005/11/COLLADASchema}triangles"
DAEp = "{http://www.collada.org/2005/11/COLLADASchema}p"

#Animation Schemas
DAELibAnims = "{http://www.collada.org/2005/11/COLLADASchema}library_animations"
DAEAnim = "{http://www.collada.org/2005/11/COLLADASchema}animation"
DAEChannel = "{http://www.collada.org/2005/11/COLLADASchema}channel"


def ColorToArrayToString(color):
    colorArray = []
    colorArray.append(color.r)
    colorArray.append(color.g)
    colorArray.append(color.b)
    colorArray = str(colorArray)
    colorArray = colorArray.translate({ord(c):None for c in '[],'})
    return colorArray

def writeTextures(dae,libImages,texName):
    thisImage = dae.ET.SubElement(libImages,'image',id=texName+'-image',name=texName)
    init = dae.ET.SubElement(thisImage,'init_from')
    print("Texture = "+texName)
    init.text = D.textures[texName].image.filepath

def writeMaterials(dae,libMats,libEffects,matName):
    thisMaterial = dae.ET.SubElement(libMats,'material',id=matName,name=matName)
    instance = dae.ET.SubElement(thisMaterial,'instance_effect',url='#'+matName+'-fx')
    
    thisEffect = dae.ET.SubElement(libEffects,'effect',id=matName+'-fx',name=matName)
    profile = dae.ET.SubElement(thisEffect,'profile_COMMON')
    technique = dae.ET.SubElement(profile,'technique',sid='standard')
    shtype = dae.ET.SubElement(technique,D.materials[matName].specular_shader.lower())
    
    #Get Textures
    diffuse_tex = []
    specular_tex = []
    emission_tex = []
    normal_tex = []
    for t in D.materials[matName].texture_slots:
        if t is not None:
            if t.use_map_color_diffuse:
                diffuse_tex.append(t)
            if t.use_map_specular:
                specular_tex.append(t)
            if t.use_map_emission:
                emission_tex.append(t)
            if t.use_map_normal:
                normal_tex.append(t)
    
    #Emission Element
    emit = dae.ET.SubElement(shtype,'emission')
    color = dae.ET.SubElement(emit,'color',sid='emission')   
    color.text = ColorToArrayToString(D.materials[matName].diffuse_color)
    if (len(emission_tex) > 0):
        for t in emission_tex:
            texture = dae.ET.SubElement(emit,'texture',texture=t.name+'-image',texcoord='CHANNEL0')
            extra = dae.ET.SubElement(texture,'extra')
            technique = dae.ET.SubElement(extra,'technique',profile='MAYA')
            wrapU = dae.ET.SubElement(technique,'wrapU',sid='wrapU0')
            wrapU.text='TRUE'
            wrapV = dae.ET.SubElement(technique,'wrapV',sid='wrapV0')
            wrapV.text='TRUE'
            blend = dae.ET.SubElement(technique,'blend_mode')
            blend.text = t.blend_type
    
    #Ambient
    ambient = dae.ET.SubElement(shtype,'ambient')
    color = dae.ET.SubElement(ambient,'color',sid='ambient')
    color.text = ColorToArrayToString(D.worlds['World'].ambient_color)+' '+str(D.materials[matName].ambient)
    
    #Diffuse
    diffuse = dae.ET.SubElement(shtype,'diffuse')
    if (len(diffuse_tex)==0):
        color = dae.ET.SubElement(diffuse,'color',sid='diffuse')
        color.text = ColorToArrayToString(D.materials[matName].diffuse_color)
    if (len(diffuse_tex)>0):
        for t in diffuse_tex:
            texture = dae.ET.SubElement(diffuse,'texture',texture=t.name+'-image',texcoord='CHANNEL0')
            extra = dae.ET.SubElement(texture,'extra')
            technique = dae.ET.SubElement(extra,'technique',profile='MAYA')
            wrapU = dae.ET.SubElement(technique,'wrapU',sid='wrapU0')
            wrapU.text='TRUE'
            wrapV = dae.ET.SubElement(technique,'wrapV',sid='wrapV0')
            wrapV.text='TRUE'
            blend = dae.ET.SubElement(technique,'blend_mode')
            blend.text = t.blend_type
    
    #Specular
    specular = dae.ET.SubElement(shtype,'specular')
    color = dae.ET.SubElement(specular,'color',sid='specular')
    color.text = ColorToArrayToString(D.materials[matName].specular_color)
    if (len(specular_tex)>0):
        for t in specular_tex:
            texture = dae.ET.SubElement(specular,'texture',texture=t.name+'-image',texcoord='CHANNEL0')
            extra = dae.ET.SubElement(texture,'extra')
            technique = dae.ET.SubElement(extra,'technique',profile='MAYA')
            wrapU = dae.ET.SubElement(technique,'wrapU',sid='wrapU0')
            wrapU.text="TRUE"
            wrapV = dae.ET.SubElement(technique,'wrapV',sid='wrapV0')
            wrapV.text = 'TRUE'
            blend = dae.ET.SubElement(technique,'blend_mode')
            blend.text = t.blend_type
    shininess = dae.ET.SubElement(shtype,'shininess')
    shine = dae.ET.SubElement(shininess,'float',sid='shininess')
    shine.text = str(D.materials[matName].specular_hardness)
    
    #Reflective
    reflective = dae.ET.SubElement(shtype,'reflective')
    color = dae.ET.SubElement(reflective,'color')
    color.text = ColorToArrayToString(D.materials[matName].mirror_color)
    
    #Transparency
    transparency = dae.ET.SubElement(shtype,'transparency')
    float = dae.ET.SubElement(transparency,'float',sid='transparency')
    float.text = str(D.materials[matName].alpha)

def writeGeometry(dae,libgeo,geoName):
    #Triangulate the Mesh
    thisGeo = dae.ET.SubElement(libgeo,'geometry',name = geoName,id=geoName)
    thisMesh = dae.ET.SubElement(thisGeo,'mesh')
    C.scene.objects.active = D.objects[geoName]
    bpy.ops.object.modifier_add(type='TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier='Triangulate')
    
    mesh = D.objects[geoName].data
    mesh.update(calc_tessface=True)
    mesh.calc_normals_split()
    
    #Create the Vertices
    vertices = []
    for v in mesh.vertices:
        vertices.append(v.co.x)
        vertices.append(v.co.y)
        vertices.append(v.co.z)    
    meshPositions = dae.ET.SubElement(thisMesh,'source',id=geoName+'-positions')
    vertArray = dae.ET.SubElement(meshPositions,'float_array',id=meshPositions.attrib['id']+'-array',count=str(len(vertices)))
    vertices = str(vertices)    
    vertArray.text = vertices.translate({ord(c):None for c in '[],'})
    technique = dae.ET.SubElement(meshPositions,'technique_common')
    accessor = dae.ET.SubElement(technique,'accessor',source='#'+vertArray.attrib['id'],count=str(len(mesh.vertices)),stride='3')
    paramX = dae.ET.SubElement(accessor,'param',name='X',type='float')
    paramY = dae.ET.SubElement(accessor,'param',name='Y',type='float')
    paramZ = dae.ET.SubElement(accessor,'param',name='Z',type='float')
    
    #Create the Normals
    normals = []
    for v in mesh.loops:
        normals.append(v.normal.x)
        normals.append(v.normal.y)
        normals.append(v.normal.z)    
    meshNormals = dae.ET.SubElement(thisMesh,'source',id=geoName+'-normals')
    normalArray = dae.ET.SubElement(meshNormals,'float_array',id=meshNormals.attrib['id']+'-array',count = str(len(normals)))
    normals = str(normals)
    normalArray.text = normals.translate({ord(c):None for c in '[],'})
    technique = dae.ET.SubElement(meshNormals,'technique_common')
    accessor = dae.ET.SubElement(technique,'accessor',source='#'+normalArray.attrib['id'],count=str(len(mesh.loops)),stride='3')
    paramX = dae.ET.SubElement(accessor,'param',name='X',type='float')
    paramY = dae.ET.SubElement(accessor,'param',name='Y',type='float')
    paramZ = dae.ET.SubElement(accessor,'param',name='Z',type='float')
    
    #Create UVs
    uvMaps = []
    for uvi in mesh.uv_layers:
        thisMap = dae.ET.SubElement(thisMesh,'source',id=geoName+'-texcoord-'+uvi.name)
        uvMaps.append(thisMap)
        coords = []
        for v in uvi.data:
            coords.append(v.uv.x)
            coords.append(v.uv.y)
        array = dae.ET.SubElement(thisMap,'float_array',id=thisMap.attrib['id']+'-array',count = str(len(coords)))
        coords = str(coords)
        array.text = coords.translate({ord(c):None for c in '[],'})
        technique = dae.ET.SubElement(thisMap,'technique_common')
        accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = str(len(uvi.data)),stride='2')
        paramS = dae.ET.SubElement(accessor,'param',name='S',type='float')
        paramT = dae.ET.SubElement(accessor,'param',name='T',type='float')
    
    #Tell it where the vertices are
    vertElement = dae.ET.SubElement(thisMesh,'vertices',id=geoName+'-vertices')
    input = dae.ET.SubElement(vertElement,'input',semantic='POSITION',source='#'+meshPositions.attrib['id'])
    
    #Make the Triangles
    if len(mesh.materials)>0:
        for m in range(0,len(mesh.materials)):
            print("+++"+str(m)+", len(mesh.materials)="+str(len(mesh.materials)))
            mat = mesh.materials[m]
            polys = []
            for p in mesh.polygons:
                if p.material_index == m:
                    polys.append(p)
            tris = dae.ET.SubElement(thisMesh,'triangles',material = mat.name,count=str(len(polys)))
            inputVert = dae.ET.SubElement(tris,'input',semantic='VERTEX',offset='0',source='#'+vertElement.attrib['id'])
            inputNormal = dae.ET.SubElement(tris,'input',semantic='NORMAL',offset ='1',source = '#'+ meshNormals.attrib['id'])
            for u in range(0,len(uvMaps)):
                map = dae.ET.SubElement(tris,'input',semantic = 'TEXCOORD',offset='1',set=str(u),source='#'+uvMaps[u].attrib['id'])
            pElement = dae.ET.SubElement(tris,'p')
            pVerts = []
            pInds = []
            for p in mesh.polygons:
                for i in p.vertices:
                    pVerts.append(i)
            for p in mesh.polygons:
                if (p.material_index==m):
                    for i in p.loop_indices:
                        pInds.append(pVerts[i])
                        pInds.append(i)
            pInds = str(pInds)
            pElement.text = pInds.translate({ord(c):None for c in '[],'})
    else:
        polys = []
        for p in mesh.polygons:
            polys.append(p)
        tris = dae.ET.SubElement(thisMesh,'triangles',count=str(len(polys)))
        inputVert = dae.ET.SubElement(tris,'input',semantic='VERTEX',offset='0',source='#'+vertElement.attrib['id'])
        inputNormal = dae.ET.SubElement(tris,'input',semantic='NORMAL',offset ='1',source = '#'+ meshNormals.attrib['id'])        
        pElement = dae.ET.SubElement(tris,'p')
        pVerts = []
        pInds = []
        for p in mesh.polygons:
            for i in p.vertices:
                pVerts.append(i)
        for p in polys:
            for i in p.loop_indices:
                pInds.append(pVerts[i])
                pInds.append(i)
        pInds = str(pInds)
        pElement.text = pInds.translate({ord(c):None for c in '[],'})
        
        
def writeAnims(dae,libanims,objName):
    
    thisAnim = dae.ET.SubElement(libanims,'animation',id=objName+'-anim',name=objName)
    
    if D.objects[objName].animation_data.action is not None:
        for curve in D.objects[objName].animation_data.action.fcurves:
            thisCurve = dae.ET.SubElement(libanims,'animation')
            print(curve.data_path+" "+str(curve.array_index))
            
            baseID = None
            
            if curve.data_path == 'location':
                baseID = objName+'-translate'
                if curve.array_index == 0:
                    baseID = baseID+'.X'
                if curve.array_index == 1:
                    baseID = baseID+'.Y'
                if curve.array_index == 2:
                    baseID = baseID+'.Z'
                    
            if curve.data_path == 'rotation_euler':
                baseID = objName+'-rotate'
                if curve.array_index == 0:
                    baseID = baseID+'X.ANGLE'
                if curve.array_index == 1:
                    baseID = baseID+'Y.ANGLE'
                if curve.array_index == 2:
                    baseID = baseID+'Z.ANGLE'
            
            if curve.data_path == 'scale':
                baseID = objName+'-scale'
                if curve.array_index == 0:
                    baseID = baseID+'.X'
                if curve.array_index == 1:
                    baseID = baseID+'.Y'
                if curve.array_index == 2:
                    baseID = baseID+'.Z'
            
            keys = []
            values = []
            interp = []
            intan = []
            outtan = []
            
            for k in curve.keyframe_points:
                keys.append(k.co.x/C.scene.render.fps)
                #if curve.data_path == 'location':
                if curve.data_path == 'location' or curve.data_path == 'scale':
                    values.append(k.co.y)
                if curve.data_path == 'rotation_euler':
                    values.append(math.degrees(k.co.y))
                interp.append(k.interpolation)
                intan.append(k.handle_left.x)
                intan.append(k.handle_left.y)
                outtan.append(k.handle_right.x)
                outtan.append(k.handle_right.y)
            
            #Sampler
            sampler = dae.ET.SubElement(thisCurve,'sampler',id=baseID)
            
            #Create the input values (keyframes)
            source = dae.ET.SubElement(thisCurve,'source',id=baseID+'-input')
            input = dae.ET.SubElement(sampler,'input',semantic = 'INPUT',source='#'+source.attrib['id'])
            array = dae.ET.SubElement(source,'float_array',id=baseID+'-input-array',count = str(len(keys)))
            array.text = str(keys).translate({ord(c):None for c in '[],'})
            technique = dae.ET.SubElement(source,'technique_common')
            accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = array.attrib['count'],stride = '1')
            param = dae.ET.SubElement(accessor,'param',type='float')
            
            #Create the output values (actual values)
            source = dae.ET.SubElement(thisCurve,'source',id=baseID+'-output')
            input = dae.ET.SubElement(sampler,'input',semantic = 'OUTPUT',source='#'+source.attrib['id'])
            array = dae.ET.SubElement(source,'float_array',id=baseID+'-output-array',count = str(len(values)))
            array.text = str(values).translate({ord(c):None for c in '[],'})
            technique = dae.ET.SubElement(source,'technique_common')
            accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = array.attrib['count'],stride = '1')
            param = dae.ET.SubElement(accessor,'param',type='float')
            
            #Create the interpolations
            source = dae.ET.SubElement(thisCurve,'source',id=baseID+'-interpolation')
            input = dae.ET.SubElement(sampler,'input',semantic='INTERPOLATION',source='#'+source.attrib['id'])
            array = dae.ET.SubElement(source,'Name_array',id=baseID+'-interpolation-array',count = str(len(interp)))
            array.text = str(interp).translate({ord(c):None for c in '[],\''})
            technique = dae.ET.SubElement(source,'technique_common')
            accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = array.attrib['count'],stride='1')
            param = dae.ET.SubElement(accessor,'param',type='name')
            
            #Intangents for Bezier Curves
            source = dae.ET.SubElement(thisCurve,'source',id=baseID+'-intan')
            input = dae.ET.SubElement(sampler,'input',semantic='IN_TANGENT',source='#'+source.attrib['id'])
            array = dae.ET.SubElement(source,'float_array',id=baseID+'-intan-array',count = str(len(intan)))
            array.text = str(intan).translate({ord(c):None for c in '[],'})
            technique = dae.ET.SubElement(source,'technique_common')
            accessor = dae.ET.SubElement(technique,'accessor',source = '#'+array.attrib['id'],count = str(len(intan)/2),stride = '2')
            paramA = dae.ET.SubElement(accessor,'param',type='float')
            paramB = dae.ET.SubElement(accessor,'param',type='float')
            
            #Outtangents for Bezier Curves
            source = dae.ET.SubElement(thisCurve,'source',id=baseID+'-outtan')
            input = dae.ET.SubElement(sampler,'input',semantic='OUT_TANGENT',source='#'+source.attrib['id'])
            array = dae.ET.SubElement(source,'float_array',id=baseID+'-outtan-array',count = str(len(outtan)))
            array.text = str(outtan).translate({ord(c):None for c in '[],'})
            technique = dae.ET.SubElement(source,'technique_common')
            accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = str(len(outtan)/2),stride = '2')
            paramA = dae.ET.SubElement(accessor,'param',type='float')
            paramB = dae.ET.SubElement(accessor,'param',type='float')
            
            channel = dae.ET.SubElement(thisCurve,'channel',source='#'+baseID,target=baseID.split('-')[0]+'/'+baseID.split('-')[1])
        
        
def writeNodes(dae,parentNode,libgeo,libanims,objectName):
    print("Writing Node for "+objectName)
    thisNode = dae.ET.SubElement(parentNode,'node',name=objectName,id=objectName,sid=objectName)
    thisPosition = dae.ET.SubElement(thisNode,'translate',sid='translate')
    thisPosition.text = str(D.objects[objectName].matrix_local.translation.x)+' '+str(D.objects[objectName].matrix_local.translation.y)+' '+str(D.objects[objectName].matrix_local.translation.z)
    rotZ = dae.ET.SubElement(thisNode,'rotate',sid='rotateZ')
    rotZ.text = '0 0 1 '+str(math.degrees(D.objects[objectName].matrix_local.to_euler().z))
    rotY = dae.ET.SubElement(thisNode,'rotate',sid='rotateY')
    rotY.text = '0 1 0 '+str(math.degrees(D.objects[objectName].matrix_local.to_euler().y))
    rotX = dae.ET.SubElement(thisNode,'rotate',sid='rotateX')
    rotX.text = '1 0 0 '+str(math.degrees(D.objects[objectName].matrix_local.to_euler().x))
    if D.objects[objectName].animation_data is not None:
        writeAnims(dae,libanims,objectName)
    if D.objects[objectName].type == 'MESH':
        geoInstance = dae.ET.SubElement(thisNode,'instance_geometry',url='#'+objectName)
        bindMat = dae.ET.SubElement(geoInstance,'bind_material')
        matTechnique = dae.ET.SubElement(bindMat,'technique_common')
        for m in D.objects[objectName].material_slots:
            matInstance = dae.ET.SubElement(matTechnique,'instance_material',symbol = m.name,target='#'+m.name)            
        writeGeometry(dae,libgeo,objectName)
    #Get Navlight Data and change append it into Node name
    if D.objects[objectName].type == 'LAMP':    
        print('Found Lamp '+objectName)
        lamp = D.objects[objectName].data
        if hasattr(lamp,'["Phase"]'): # Need to pick up on "Phase" to avoid confusion with BackgroundLights -- Dom2
            print('Found NavLight')
            lampColorR = str(lamp.color.r)
            lampColorG = str(lamp.color.g)
            lampColorB = str(lamp.color.b)
            lampSize = str(lamp.energy)
            lampDist = str(lamp.distance)
            lampPhase = str(lamp["Phase"])
            lampFreq = str(lamp["Freq"])
            lampType = lamp["Type"]
            
            newName = objectName+'_Type['+lampType+']_Sz['+lampSize+']_Ph['+lampPhase+']_Fr['+lampFreq+']_Col['+lampColorR+','+lampColorG+','+lampColorB+']_Dist['+lampDist+']'
            
            if hasattr(lamp,'["Flags"]'):
                lampFlags = lamp["Flags"]
                newName = newName+'_Flags['+lampFlags+']'
            
            print(newName)
            thisNode.set('id',newName)
            thisNode.set('name',newName)   
            thisNode.set('sid',newName)
            
        elif hasattr(lamp,'["Atten"]'): # Need to pick up on "Atten" to avoid confusion with NavLights -- Dom2
            print('Found BackgroundLight')
            lampColorR = str(lamp.color.r)
            lampColorG = str(lamp.color.g)
            lampColorB = str(lamp.color.b)
            # Not sure how to grab the spec yet...
            #lampSpecR = str(lamp.specular.r)
            #lampSpecG = str(lamp.specular.g)
            #lampSpecB = str(lamp.specular.b)
            lampAtten = lamp["Atten"]
            lampType = lamp["Type"]
            
            newName = objectName+'_Type['+lampType+']_Diff['+lampColorR+','+lampColorG+','+lampColorB+']_Spec[0,0,0]_Atten['+lampAtten+']'
            
            print(newName)
            thisNode.set('id',newName)
            thisNode.set('name',newName)   
            thisNode.set('sid',newName)
            
    #Parse Dock Node Data and append to name
    if 'DOCK[' in objectName:
        print("Found Dock path "+objectName)
        dockNode = D.objects[objectName]
        if hasattr(dockNode,'["Fam"]'):
            shipFam = dockNode['Fam']
            newName = objectName+'_Fam['+shipFam+']'
            if hasattr(dockNode,'["Link"]'):
                dockLink = dockNode["Link"]
                newName = newName+'_Link['+dockLink+']'
            if hasattr(dockNode,'["Flags"]'):
                dockFlags = dockNode["Flags"]
                newName = newName+'_Flags['+dockFlags+']'
            if hasattr(dockNode,'["MAD"]'):
                dockMAD = str(dockNode["MAD"])
                newName = newName+'_MAD['+dockMAD+']'
            
            thisNode.set('id',newName)
            thisNode.set('name',newName)
            thisNode.set('sid',newName)
     
    #Parse Seg Nodes
    if 'SEG[' in objectName:
        segNode = D.objects[objectName]
        if hasattr(segNode,'["Speed"]'):
            newName = objectName.split('.')[0]
            segTol = str(int(segNode.empty_draw_size))
            segSpeed = str(segNode["Speed"])
            newName = newName+'_Tol['+segTol+']_Spd['+segSpeed+']'
            if hasattr(segNode,'["Flags"]'):
                segFlags = segNode["Flags"]
                newName = newName+'_Flags['+segFlags+']'
            
            thisNode.set('id',newName)
            thisNode.set('name',newName)
            thisNode.set('sid',newName)
    
    #Parse MAT[xxx]_PARAM[yyy] Nodes
    if 'MAT[' in objectName and 'PARAM[' in objectName:
        print("This is a MAT[xxx]_PARAM[yyy] joint...")
        matPexNode = D.objects[objectName]
        newName = objectName.split('.')[0] # in case it is "MAT[xxx]_PARAM[yyy]_Type[RGBA].001"
        print(str(newName))
        """
        if hasattr(matPexNode,'["Type6"]'):
            matPEXtype = str(matPexNode["Type6"])
            newName = newName+'_Type6['+matPEXtype+']'
        if hasattr(matPexNode,'["Type"]'):
            matPEXtype = str(matPexNode["Type"])
            newName = newName+'_Type['+matPEXtype+']'
        """
        # If the joint has custom properties, build them into the name
        if len(matPexNode.keys())>1:
            newName = newName + "_Data["
            for p in matPexNode.keys():
                print("found parameter " + str(p))
                if p.startswith("data"):
                    print("it is a data paramter")
                    if newName.endswith("["):
                        newName = newName + str(matPexNode[p])
                    else:
                        newName = newName + "," + str(matPexNode[p])
            newName = newName + "]" # Joint name should now be "MAT[xxx]_PARAM[yyy]_Type[RGBA]_Data[i,k,j]"

        thisNode.set('id',newName)
        thisNode.set('name',newName)
        thisNode.set('sid',newName)
    
    if D.objects[objectName].children is not None:
        for c in D.objects[objectName].children:
            writeNodes(dae,thisNode,libgeo,libanims,c.name)

def prettify(element, indent='  '):
    queue = [(0, element)]  # (level, element)
    while queue:
        level, element = queue.pop(0)
        children = [(level + 1, child) for child in list(element)]
        if children:
            element.text = '\n' + indent * (level+1)  # for child open
        if queue:
            element.tail = '\n' + indent * queue[0][0]  # for sibling open
        else:
            element.tail = '\n' + indent * (level-1)  # for parent close
        queue[0:0] = children  # prepend so children come before siblings  




class HwDAE:
    import xml.etree.ElementTree as ET
    
    
    
    def doExport(self,filepath):
        
        
        #Set up Collada Header Stuff
        print('Writing Root')
        root = self.ET.Element('COLLADA',version='1.4.1',xmlns = 'http://www.collada.org/2005/11/COLLADASchema')
        asset = self.ET.SubElement(root,'asset')
        contributorTag = self.ET.SubElement(asset,'contributor')
        contribAuthor = self.ET.SubElement(contributorTag,'author')
        contribAuthor.text = 'Anonymous'
        contribTool = self.ET.SubElement(contributorTag,'authoring_tool')
        contribTool.text = 'New Collada Exporter for Blender, by David Lejeune'
        createdDate = self.ET.SubElement(asset,'created')
        createdDate.text = time.ctime()
        modifiedDate = self.ET.SubElement(asset,'modified')
        modifiedDate.text = time.ctime()
        units = self.ET.SubElement(asset,'unit',meter='1.0',name='meter')
        upAxis = self.ET.SubElement(asset,'up_axis')
        upAxis.text = 'Z_UP'

        #Write the Library Visual Scenes Stuff
        print('Writing Library Visual Scenes')
        libScenes = self.ET.SubElement(root,'library_visual_scenes')    
        thisScene = self.ET.SubElement(libScenes,'visual_scene',id=C.scene.name+'-id',name=C.scene.name)
        daeScene = self.ET.SubElement(root,'scene')
        visScene = self.ET.SubElement(daeScene,'instance_visual_scene',url='#'+thisScene.attrib["id"])
    
        print('Writing Library Images')
        libImages = self.ET.SubElement(root,'library_images')
        print('Writing Library Materials')
        libMats = self.ET.SubElement(root,'library_materials')
        print('Writing Library Effects')
        libEffects = self.ET.SubElement(root,'library_effects')
        print('Writing Library Geometries')
        libGeometries = self.ET.SubElement(root,'library_geometries')
        print('Writing Library Animations')
        libAnimations = self.ET.SubElement(root,'library_animations')
    
        for ob in D.objects:
            if ob.parent is None:
                writeNodes(self,thisScene,libGeometries,libAnimations,ob.name)
    
        for mat in D.materials:
            #Set Phong
            D.materials[mat.name].specular_shader = "PHONG"
            writeMaterials(self,libMats,libEffects,mat.name)   

        for tex in D.textures:
            if hasattr(tex,'image'):
                writeTextures(self,libImages,tex.name)
        
        prettify(root)
        doc = self.ET.ElementTree(root)
#doc.write('F:\\mymod\\Test.dae',encoding = 'utf-8',xml_declaration=True)

        print(filepath)
        doc.write(filepath,encoding='utf-8',xml_declaration=True)
    
    def __init__(self):
        self.data = []
        
    
def save(filepath): 

    thisDAE = HwDAE()
   
    thisDAE.doExport(filepath)
    
    return{'FINISHED'}
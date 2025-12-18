import bpy
import math
from mathutils import Vector, Euler

# TELESCOPE + OBSERVATION PARAMETERS 
aperture_mm = 406.4  
f_number = 10
focal_length_mm = aperture_mm * f_number  
wavelength_nm = 550
pixel_size_um = 4.63
range_km = 1262
phase_angle_deg = 40.8598
azimuth_deg = 39.2924
elevation_deg = 51.0299
gain = 2680
satellite_velocity = 7350  
feature_size_m = 1.5
output_path = "Enter the desired file location.png"

# CONVERSIONS 
range_m = range_km * 1000
focal_length_m = focal_length_mm / 1000
aperture_m = aperture_mm / 1000
wavelength_m = wavelength_nm * 1e-9
pixel_size_m = pixel_size_um * 1e-6

# ATMOSPHERIC REFRACTION CORRECTION 
R_arcmin = 1.02 / math.tan(math.radians(elevation_deg) + 10.3 / (math.radians(elevation_deg) + 5.11))
R_deg = R_arcmin / 60
corrected_elevation_deg = elevation_deg + R_deg

# POSITION 
az_rad = math.radians(azimuth_deg)
el_rad = math.radians(corrected_elevation_deg)
scene_scale = 0.0001
x = range_m * scene_scale * math.cos(el_rad) * math.sin(az_rad)
y = range_m * scene_scale * math.cos(el_rad) * math.cos(az_rad)
z = range_m * scene_scale * math.sin(el_rad)
acs3_position = Vector((x, y, z))

# FIND SATELLITE 
acs3_collection = bpy.data.collections.get("acs3")
if not acs3_collection:
    raise ValueError("Collection 'acs3' not found in the scene.")

# SCALE BASED ON QUALITY FACTOR 
blur_spot = (wavelength_m * focal_length_m) / aperture_m  
quality_factor = blur_spot / feature_size_m
satellite_scale = max(quality_factor, 0.01)

for obj in acs3_collection.objects:
    obj.scale = (satellite_scale, satellite_scale, satellite_scale)
    obj.location = acs3_position
    obj.rotation_euler = Euler((math.radians(-phase_angle_deg), 0, 0), 'XYZ')
    obj.hide_render = False

# CAMERA SETUP 
cam_data = bpy.data.cameras.new("TelescopeCamera")
cam_data.lens = focal_length_mm
cam_data.sensor_width = 36
cam_data.clip_start = 0.1
cam_data.clip_end = 1e6

camera = bpy.data.objects.new("TelescopeCamera", cam_data)
bpy.context.scene.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera.location = Vector((0, 0, 0))

# ENABLE DEPTH OF FIELD 
#camera.data.dof.use_dof = True
#camera.data.dof.focus_distance = range_m  
#camera.data.dof.aperture_fstop = f_number 

direction = (acs3_position - camera.location).normalized()
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# SUN LIGHT 
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun = bpy.data.objects.new(name="Sun", object_data=sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = Euler((math.radians(90 - phase_angle_deg), 0, 0), 'XYZ')
sun.location = acs3_position + Vector((0, 0, 1000))

# MATERIALS 
sail_mat = bpy.data.materials.new(name="SilverSail")
sail_mat.use_nodes = True
nodes = sail_mat.node_tree.nodes
principled = nodes.get("Principled BSDF")
principled.inputs["Base Color"].default_value = (0.8, 0.8, 0.9, 1)
principled.inputs["Roughness"].default_value = 0.5
principled.inputs["Metallic"].default_value = 0.6

carbon_mat = bpy.data.materials.new(name="CarbonBoom")
carbon_mat.use_nodes = True
nodes2 = carbon_mat.node_tree.nodes
principled2 = nodes2.get("Principled BSDF")
principled2.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1)
principled2.inputs["Roughness"].default_value = 0.8
principled2.inputs["Metallic"].default_value = 0.0

#  Assign materials based on object name
for obj in acs3_collection.objects:
    if obj.type == 'MESH':
        obj.data.materials.clear()
        if "boom" in obj.name.lower():
            obj.data.materials.append(carbon_mat)
        else:
            obj.data.materials.append(sail_mat)

# WORLD 
world = bpy.context.scene.world
world.use_nodes = True
bg = world.node_tree.nodes
bg["Background"].inputs[0].default_value = (0, 0, 0, 1)
bg["Background"].inputs[1].default_value = 0.0
bpy.context.scene.render.film_transparent = False

# RENDER SETTINGS 
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = output_path
scene.view_settings.exposure = math.log(gain / 4000)

# COMPOSITOR: DIFFRACTION + ATMOSPHERIC + MOTION BLUR 
scene.use_nodes = True
tree = scene.node_tree
tree.nodes.clear()

# Compositing Nodes 
rlayers = tree.nodes.new("CompositorNodeRLayers")
blur = tree.nodes.new("CompositorNodeBlur")
blur.filter_type = 'GAUSS'
blur.use_relative = False

# Blur computation
theta_rad = 1.22 * wavelength_m / aperture_m
exposure_time = 1 / 1000
angular_speed = satellite_velocity / range_m
motion_blur_angle = angular_speed * exposure_time
pixel_blur = (motion_blur_angle * theta_rad * focal_length_m) / (cam_data.sensor_width / scene.render.resolution_x)
seeing_blur_px = 8
total_blur = pixel_blur + seeing_blur_px
blur.size_x = blur.size_y = int(total_blur)

# Chromatic Aberration 
sep_rgb = tree.nodes.new("CompositorNodeSepRGBA")
trans_r = tree.nodes.new("CompositorNodeTranslate")
trans_r.inputs[1].default_value = 1.0  # X shift
trans_r.inputs[2].default_value = 1.0  # Y shift

comb_rgb = tree.nodes.new("CompositorNodeCombRGBA")
tree.links.new(rlayers.outputs["Image"], sep_rgb.inputs["Image"])
tree.links.new(sep_rgb.outputs["R"], trans_r.inputs["Image"])
tree.links.new(trans_r.outputs["Image"], comb_rgb.inputs["R"])
tree.links.new(sep_rgb.outputs["G"], comb_rgb.inputs["G"])
tree.links.new(sep_rgb.outputs["B"], comb_rgb.inputs["B"])

# Glare (Bloom)
glare = tree.nodes.new("CompositorNodeGlare")
glare.glare_type = 'FOG_GLOW'
glare.quality = 'LOW'
glare.size = 2

# Sensor Noise 
# Step 1: Create a noise texture in data
noise_texture = bpy.data.textures.new("NoiseTex", type='CLOUDS')
noise_texture.noise_scale = 0.2  # Control scale of noise

# Step 2: Use CompositorNodeTexture to bring it in
noise_node = tree.nodes.new("CompositorNodeTexture")
noise_node.texture = noise_texture

# Step 3: Mix with image using overlay
mix_noise = tree.nodes.new("CompositorNodeMixRGB")
mix_noise.blend_type = 'OVERLAY'
mix_noise.inputs[0].default_value = 0.05  

mix_noise = tree.nodes.new("CompositorNodeMixRGB")
mix_noise.blend_type = 'OVERLAY'
mix_noise.inputs[0].default_value = 0.05

# Final Composite Output 
comp = tree.nodes.new("CompositorNodeComposite")

# Connections 
tree.links.new(comb_rgb.outputs["Image"], blur.inputs["Image"])
tree.links.new(blur.outputs["Image"], glare.inputs["Image"])
tree.links.new(glare.outputs["Image"], mix_noise.inputs[1])
tree.links.new(noise_node.outputs["Color"], mix_noise.inputs[2])
tree.links.new(mix_noise.outputs["Image"], comp.inputs["Image"])


# FINAL RENDER 
bpy.ops.render.render(write_still=True)

# PRINT RESULTS
print("Render complete.")
print(f"Corrected elevation: {corrected_elevation_deg:.2f}°")
print(f"Satellite scale: {satellite_scale:.4f}")
print(f"Diffraction blur (Airy disk): {pixel_blur:.2f} px")

def part_volumes_to_part_groups(prefix=None): 
  """
  Create a group for each volume in Cubit and add the volume to its group
  
  This is useful when working with assemblies, as the group structuring
  is retained throughout webcutting for eventual hex-meshing.
  This makes it easier to apply operations onto entire 'parts', such as
  imprint and merge operations.

  Parameters
  ----------
  prefix : str
      Defines the prefix to be used in group name.
      Defaults to 'part'

  Results
  ----------
  New Cubit 'group' entities with names of the form: prefix_id

  Examples
  ----------
  part_volumes_to_part_groups()
    --> groups with names: part_1, part_2, part_40, ...
  part_volumes_to_part_groups(prefix='component')
    --> groups with names: component_1, component_2, component_40, ...
  """
  
  if prefix == None:
    prefix = "part"
  V = cubit.get_entities("volume")
  for vid in V:
    cubit.cmd(f"create group '{prefix}_{vid}'")
    cubit.cmd(f"{prefix}_{vid} add volume {vid}")

def imprint_merge_each_group():
  """
  Cycle through each group in Cubit and apply imprint and merge operations

  This script is intended to work in conjunction with the `part_volumes_to_part_groups()`
  method provided above, to simplify imprint and merge mesh operations on assemblies.
  """
  
  G = cubit.get_entities("group")
  for gid in G:
    vid = cubit.get_group_volumes(gid)
    if len(vid)>1:
      cubit.cmd(f"imprint vol {list_to_str(vid)}")
      cubit.cmd(f"merge vol {list_to_str(vid)}")

def list_to_str(input_str):
  """
  Convert a Python list or tuple into a Cubit-compatible string

  This method accepts a list or tuple (the latter often returned by Cubit functions)
  and converts it into a space-separated string that cubit.cmd() can use as input.
  This is very basic functionality that only produces valid output on lists/tuples
  that have no nesting.
  This method is primarily meant to operate with various Cubit methods via f-strings
  and largely duplicates the current built-in Cubit method: `string_from_id_list()` 
  which currently has a bug.

  Parameters
  ----------
  input_str : list or tuple (or similar Python datatype)

  Returns
  ----------
  Space-delimited string

  Example
  ----------
  cubit.cmd('reset')
  cubit.cmd('brick x 1')
  cubit.cmd('volume 1 copy move x 2 repeat 9')
  vid = cubit.get_entities("volume")
  cubit.cmd(f'block 1 volume {list_to_str(vid)}')
  """

  return " ".join([str(val) for val in input_str])

def batch_remove_overlaps_from_volume( modify_volume_id, max_gap=0.0005, max_angle=5.0 ):
  """
  Removes all overlaps from a volume.

  This method accepts an integer of a volume from which the user wishes to remove overlaps.
  This method also allows the user to optionally specify the 'Max Gap' and `Max Gap Angle`,
  which are the two settings the user can control in the `Manage Gaps and Volume Overlaps`
  GUI command panel.  
  Note that if the user *doesn't* provide these arguments then this routine will use the 
  same factory-default settings as in the GUI, and *will overwrite* any settings the user
  may have already specified.
  Thus, if the user wants to use non-default settings *the user must provide these inputs*.

  Parameters
  ----------
  modify_volume_id : integer 
    id of the volume to remove overlaps from
  max_gap : float
    the max gap value for calculating surface overlaps
  max_gap_angle : float
    the max gap angle, in degrees, for calculating surface overlaps

  Returns
  ----------
  None

  Example
  ----------
  cubit.cmd('reset')
  cubit.cmd('brick x .1 y 0.01 z .4')
  cubit.cmd('Volume all copy move x .12 y 0 z 0 repeat 9 nomesh ')
  cubit.cmd('Volume all copy move x 0 y 0 z 0.42 repeat 9 nomesh ')
  cubit.cmd('create brick bounding box Volume all extended absolute .1')
  cubit.cmd('move volume 101 y 0.105')
  batch_remove_overlaps_from_volume( 101, max_gap=0.0005, max_angle=5.0 )
  """
  cubit.set_overlap_max_gap( max_gap )
  cubit.set_overlap_max_angle( max_angle )
  V = cubit.get_overlapping_volumes_at_volume( modify_volume_id, cubit.get_entities( "volume" ) )
  for vid in V:
    cubit.cmd( f"remove overlap volume {vid} {modify_volume_id} modify volume {modify_volume_id}" )

def count_acis_entity_types():
  """
  Counts the amount of ACIS entity types, prints and returns findings.

  This method queries every surface and curve in the active model and
  counts the total amounts of the different ACIS entity types.
  The method then prints the count summaries to the terminal.
  The method also returns the entity ids within a nested tuple to enable
  deeper investigation.

  Parameters
  ----------
  None

  Returns
  ----------
  A tuple of tuples of lists of the entity ids of each entity type
    ( (tuple_of_surface_type_lists), (tuple_of_curve_type_lists) )
  where:
    tuple_of_surface_type_lists: ( plane_list, cone_list, sphere_list, torus_list, spline_list )
    tuple_of_curve_type_lists:   ( straight_list, arc_list, ellipse_list, spline_list )

  Example
  ----------
  cubit.cmd('reset')
  cubit.cmd('bri x 1')
  cubit.cmd('create frustum height 1 radius 0.3 top 0')
  cubit.cmd('create sphere radius 1')
  cubit.cmd('create torus major radius 1 minor radius 0.1')
  cubit.cmd('create sphere radius 1')
  cubit.cmd('Volume 5 scale X 1 Y 2 Z 3 ')
  cubit.cmd('split periodic volume all')
  counts = count_acis_entity_types()
  
  # Prints:
  Number of Plane  Surfaces: 7
  Number of Cone   Surfaces: 2
  Number of Sphere Surfaces: 2
  Number of Torus  Surfaces: 4
  Number of Spline Surfaces: 2
  Number of Straight Curves: 14
  Number of Arc      Curves: 12
  Number of Ellipse  Curves: 1
  Number of Spline   Curves: 1
  
  # Returns
  counts = ( ( [1, 2, 3, 4, 5, 6, 8], 
               [12, 13], 
               [14, 15], 
               [16, 17, 18, 19], 
               [20, 21]), 
             ( [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 17], 
               [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29], 
               [15], 
               [30] ) 
            )
  """
  S = cubit.get_entities("surface")
  C = cubit.get_entities("curve")
  # Process Surfaces
  plane_surf = []
  cone_surf = []
  sphere_surf = []
  torus_surf = []
  spline_surf = []
  for sid in S:
    surf_type = cubit.get_surface_type( sid ).lower()
    if surf_type == "plane surface":
      plane_surf.append( sid )
    elif surf_type == "cone surface":
      cone_surf.append( sid )
    elif surf_type == "sphere surface":
      sphere_surf.append( sid )
    elif surf_type == "torus surface":
      torus_surf.append( sid )
    elif surf_type == "spline surface":
      spline_surf.append( sid )
  # Process Curves
  straight_curve = []
  arc_curve = []
  ellipse_curve = []
  spline_curve = []
  for cid in C:
    curve_type = cubit.get_curve_type( cid ).lower()
    if curve_type == "straight curve":
      straight_curve.append( cid )
    elif curve_type == "arc curve":
      arc_curve.append( cid )
    elif curve_type == "ellipse curve":
      ellipse_curve.append( cid )
    elif curve_type == "spline curve":
      spline_curve.append( cid )
  ## Print Results
  out_str  = f"Number of Plane  Surfaces: {len( plane_surf )}\n" 
  out_str += f"Number of Cone   Surfaces: {len( cone_surf )}\n" 
  out_str += f"Number of Sphere Surfaces: {len( sphere_surf )}\n" 
  out_str += f"Number of Torus  Surfaces: {len( torus_surf )}\n" 
  out_str += f"Number of Spline Surfaces: {len( spline_surf )}\n" 
  out_str += f"Number of Straight Curves: {len( straight_curve )}\n"
  out_str += f"Number of Arc      Curves: {len( arc_curve )}\n"
  out_str += f"Number of Ellipse  Curves: {len( ellipse_curve )}\n"
  out_str += f"Number of Spline   Curves: {len( spline_curve )}\n"
  print( out_str )
  return ( ( plane_surf, cone_surf, sphere_surf, torus_surf, spline_surf ), 
          ( straight_curve, arc_curve, ellipse_curve, spline_curve ) )

def color_spline_surfaces():
  """
  Colors all spline surfaces red while non-spline surfaces colored white.

  This method queries every surface in the active model and colors it red
  if it is a spline surface or white if it is not a spline surface.
  The method also replaces or creates a group with name 'spline_surfaces'
  to which all the spline surfaces are added.

  Parameters
  ----------
  None

  Returns
  ----------
  No return values
  Replaces or creates a group with name 'spline_surfaces' containing all found spline surfaces
  Colors the spline surfaces red and non-spline surfaces white

  Example
  ----------
  cubit.cmd('reset')
  cubit.cmd('bri x 1')
  cubit.cmd('create frustum height 1 radius 0.3 top 0')
  cubit.cmd('create sphere radius 1')
  cubit.cmd('create torus major radius 1 minor radius 0.1')
  cubit.cmd('create sphere radius 1')
  cubit.cmd('Volume 5 scale X 1 Y 2 Z 3 ')
  cubit.cmd('split periodic volume all')
  color_spline_surfaces()

  """
  cubit.cmd( "color surface all default" )
  if cubit.get_id_from_name( "spline_surfaces" ):
    cubit.cmd( "delete spline_surfaces" )
  cubit.cmd( "create group 'spline_surfaces'" )
  S = cubit.get_entities("surface")
  spline_surf = []
  for sid in S:
    surf_type = cubit.get_surface_type( sid ).lower()
    if surf_type == "spline surface":
      spline_surf.append( sid )
      cubit.cmd( f"color surface {sid} red" )
    else:
      cubit.cmd( f"color surface {sid} white" )
  cubit.cmd( f"spline_surfaces add surface {list_to_str( spline_surf )}" )

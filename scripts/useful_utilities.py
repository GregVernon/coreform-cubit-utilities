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


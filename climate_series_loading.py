'''
Created on Apr 15, 2013

@author: itpp

Grib climate-means project.
Code to identify+load climate series.

'''

import datetime
import glob
import numpy as np
import os
import os.path

import iris

# local modules
import grab_andys_file_summary as gafs
import test_basic_load_and_timings as blt
import simple_translations_grib1 as stg1

# private cache of gafs data
_gribmsg_data_array = None


def fetch_gribmsg_info():
    global _gribmsg_data_array
    if _gribmsg_data_array is None:
        _gribmsg_data_array = gafs.gribmsg_data_as_recarray(
            gafs.default_summary_file_path)
    return _gribmsg_data_array


def files_and_constraint_for_param_and_level(param, level):
    # Make id string for errors
    err_prefix = 'Error constraining by param={}, level={}:\n'.format(
        param, level)
    # Check given settings against message makeup info
    msgs = fetch_gribmsg_info()
    param_str = str(param)
    msgs = msgs[np.where(msgs.indicatorOfParameter == param_str)]
    if len(msgs) < 1:
        raise ValueError(err_prefix + 'Unrecognised indicatorOfParameter : '
                         + param_str)
    level_str = str(level)
    levels = sorted(set(msgs.level))
    if len(levels) == 1:
        level_str = levels[0]
    elif level_str not in levels:
        raise ValueError(err_prefix
                         + 'Unrecognised level value {}, '
                         'expected one of : {}'.format(level, levels))
    msgs = msgs[np.where(msgs.level == level_str)]
    if len(msgs) != 360:
        raise Exception(err_prefix
                        + 'Expected 360 results, got {} ?'.format(len(msgs)))
#    param_num = int(param)
#    constraint = iris.AttributeConstraint(indicatorOfParameter=param_num)
    grib1_data = stg1.identify_known_ecmwf_key(int(param))
    constraint = iris.Constraint(grib1_data.longname)
    if len(levels) > 1:
        level_constraint = iris.Constraint(pressure=int(level))
        constraint = constraint & level_constraint
    # list all the files
    file_names = sorted(set(msgs.filename))
    file_paths = [os.path.join(blt.climdir_path, file_name)
                  for file_name in file_names]
    return file_paths, constraint


#def load_callback_add_iop(cube, field, filename):
#    cube.attributes['indicatorOfParameter'] = field.indicatorOfParameter


def cube_for_param_and_level(param, level=None, debug=True):
    """
    Load a single data series into a cube.

    Args:
    * param (int):
        Grib indexOfParameter code identifying data

    Kwargs:
    * level (int):
        level to select (required for by-level codes)
    * debug (bool):
        print progress messages

    Returns:
        A single cube
    """
    if debug:
        print 'Getting series cube ({}, {})'.format(param, level)
    files, constraint = files_and_constraint_for_param_and_level(param, level)
    if debug:
        print '  files = ', files
        print '  constraint = ', constraint
        print 'Loading...'
    cubes, timer = blt.timeit_raw(files, constraint)
#                                  callback=load_callback_add_iop)
    if debug:
        print 'Result : {} cubes'.format(len(cubes))
        print 'Merging...'
    cubelist = iris.cube.CubeList(cubes).merge()
    print 'Done, n-cubes = ', len(cubelist)
    return cubelist[0]


def enumerate_all_results():
    """
    List all the target outputs over all known parameter types + levels.

    Return a list of (param, level, target_id), where target_id is a unique
    string for each output, based on parameter plus level if required.

    """
    msgs = fetch_gribmsg_info()
    param_strs = set(msgs.indicatorOfParameter)
    params = sorted([int(param_str) for param_str in param_strs])
    results = []
    for param in params:
        param_str = str(param)
        param_msgs = msgs[np.where(msgs.indicatorOfParameter == param_str)]
        all_shortnames = set(param_msgs.shortName)
        assert len(all_shortnames) == 1
        shortname, = all_shortnames
        level_strs = set(param_msgs.level)
        levels = sorted([int(level_str) for level_str in level_strs])
        for level in levels:
            target_id = shortname
            if len(levels) > 1:
                level_str = str(level)
                target_id += '_p{pressure:s}'.format(pressure=level_str)
            entry = (param, level, target_id)
            results.append(entry)
    return results


def pickout_spec(param, level=None):
    aspecs = np.array(enumerate_all_results())
    aspecs = aspecs[np.where(aspecs[:, 0] == str(param))]
    if level is not None:
        aspecs = aspecs[np.where(aspecs[:,1 ] == str(level))]
    assert aspecs.shape[1] == 3
    n_found = aspecs.shape[0]
    if n_found != 1:
        raise ValueError('Pickout(param={}, level={}) '
                         'found {} results instead of 1 ?'.format(
                             param, level, n_found))
    return aspecs[0]


def test():
#    spec = pickout_spec(186)
    spec = pickout_spec(157, 850)
    cube = cube_for_param_and_level(param=spec[0], level=spec[1])
    print cube
#    results = enumerate_all_results()
#    print '\n'.join([str(entry) for entry in results])
    t_dbg = 0

if __name__ == '__main__':
    test()

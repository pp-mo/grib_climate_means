'''
Created on Apr 17, 2013

@author: itpp

Grib climate-means project.
Code to load, aggregate and output grib climate data.

'''
import os.path
import pickle

import numpy as np

import iris.coord_categorisation

# local includes
import test_basic_load_and_timings as blt
import climate_series_loading as csl


def make_monthly_means_cube(all_times_cube, debug=True):
    with blt.TimedBlock() as t:
        iris.coord_categorisation.add_month_shortname(
            all_times_cube,
            all_times_cube.coord("time"))
        month_means = all_times_cube.aggregated_by(['month'],
                                                   iris.analysis.MEAN)
    if debug:
        print '  Aggregation time : ', t.seconds()
    return month_means

def hack_to_make_saveable(data_cube):
    z_coords = data_cube.coords(axis='z')
    if len(z_coords) == 1:
        # bug means type must be tweaked
        z_coord = z_coords[0]
        z_coord.points = z_coord.points.astype(np.float)
    elif len(z_coords) == 0:
        # fake a level coordinate
        pass

default_output_dirpath = '/net/home/h05/itpp/Iris/climate_means/temp_outputs'

def main(output_dirpath=default_output_dirpath,
         series_specs=None,
         save_as_cubes=False,
         load_from_cubes=False):
    """
    Process series to get monthly means cubes, and save these as Grib2.

    Kwargs:
    * output_dirpath (string):
        Set path of output directory.  (Default: standard output dir)
    * series_specs (list):
        A list of triples ((int)param, (int)level, (string)id_name)
        (Default: *all* series).
    * save_as_cubes (bool):
        Save as pickled cubes *instead* of Grib. (In output directory)
    * load_from_cubes (bool):
        Load from pickled cubes instead of source. (In output directory)

    """
    if series_specs is None:
        series_specs = csl.enumerate_all_results()
    for param, level, target_id in series_specs:
        gribfile_name = 'MonthlyMeans_{}.grib2'.format(target_id)
        cubefile_name = 'MonthlyMeans_{}.cube.pkl'.format(target_id)
        print '\nDoing : ', target_id
        if load_from_cubes:
            file_path = os.path.join(output_dirpath, cubefile_name)
            print '  loading aggregated from {} ..'.format(file_path)
            with open(file_path, 'r') as f:
                data_cube = pickle.load(f)
        else:
            print '  loading raw from sources ..'
            data_cube = csl.cube_for_param_and_level(param, level)
            print '  aggregating ..'
            data_cube = make_monthly_means_cube(data_cube)
        if save_as_cubes:
            file_path = os.path.join(output_dirpath, cubefile_name)
            print '  saving aggregate to \'{}\' ...'.format(file_path)
            with open(file_path, 'w') as f:
                pickle.dump(data_cube, f)
        else:
            print '  hacking level ..'
            hack_to_make_saveable(data_cube)
            file_path = os.path.join(output_dirpath, gribfile_name)
            print '  saving to \'{}\' ...'.format(file_path)
            iris.save(data_cube, file_path)

def pickout_spec(param, level=None):
    aspecs = np.array(csl.enumerate_all_results())
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

if __name__ == '__main__':
#    test_series = None
#    test_series = [pickout_spec(157, 850)]
#    test_series = [pickout_spec(186)]
    test_series = [pickout_spec(167)]
#    # NOTE: this fails in grib-pdt-deduce because latest transform is on 'month' not time
    main(series_specs=test_series)  # , load_from_cubes=True)

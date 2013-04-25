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

def hack_forecast_times(cube):
    """ Replace empty forecast_period with a sequence of startyear-months. """
    cube.remove_coord('forecast_period')
    co_t = cube.coord('time')
    # Calculate relative month start-times
    month_times = co_t.bounds[:, 0].copy()
    month_times -= month_times[0]
    # Infer delta-time units from absolute-time units
    # E.G. 'hours since  YYYY-MM-DD hh:mm:ss' --> 'hours'
    time_unit = str(co_t.units).split()[0]  
    # Create new forecast_period coord with month-start-offsets in it
    co_fp = iris.coords.DimCoord(
        points=month_times,
        standard_name='forecast_period',
        units=time_unit
        )
    cube.add_aux_coord(co_fp, 0)

def make_output_gribfile_name(cube):
    # calculate suitable filename
    co_t = cube.coord('time')
    min_year, max_year = [co_t.units.num2date(x).year
                          for x in (co_t.bounds[0,0], co_t.bounds[-1,1])]
    param_str = cube.name()
    press_coords = cube.coords('pressure')
    height_coords = cube.coords('height')
    assert len(press_coords) == 0 or len(height_coords) == 0
    if len(height_coords) > 0:
        param_str += '_h{:.0f}'.format(height_coords[0].points[0])
    if len(press_coords) > 0:
        param_str += '_p{:.0f}'.format(press_coords[0].points[0])
    gribfile_name_template = \
        'ERAI_{minyr}to{maxyr}_MonthlyMean_{param}.grib2'
    gribfile_name = gribfile_name_template.format(
        param=param_str,
        minyr=str(min_year),
        maxyr=str(max_year))
    return gribfile_name

default_output_dirpath = '/net/home/h05/itpp/Iris/climate_means/outputs'

def main(output_dirpath=default_output_dirpath,
         series_specs=None,
         save_as_grib=True,
         save_as_cubes=False,
         load_from_cubes=False,
         ):
    """
    Process series to get monthly means cubes, and save these as Grib2.

    Kwargs:
    * output_dirpath (string):
        Set path of output directory.  (Default: standard output dir)
    * series_specs (list):
        A list of triples ((int)param, (int)level, (string)id_name)
        (Default: *all* series).
    * save_as_grib (bool):
        Save to Grib2 outputs. (In output directory)
    * save_as_cubes (bool):
        Save as pickled cubes. (In output directory)
    * load_from_cubes (bool):
        Load from pickled cubes instead of source.

    """
    if series_specs is None:
        series_specs = csl.enumerate_all_results()
    for param, level, target_id in series_specs:
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
            print '  fix forecast periods ..'
            hack_forecast_times(data_cube)
            print '  result ...'
            print data_cube
        if save_as_cubes:
            file_path = os.path.join(output_dirpath, cubefile_name)
            print '  saving aggregate to \'{}\' ...'.format(file_path)
            with open(file_path, 'w') as f:
                pickle.dump(data_cube, f)
        if save_as_grib:
            print '  hacking level ..'
            hack_to_make_saveable(data_cube)
            gribfile_name = make_output_gribfile_name(data_cube)
            file_path = os.path.join(output_dirpath, gribfile_name)
            print '  saving to \'{}\' ...'.format(file_path)
            iris.save(data_cube, file_path)


if __name__ == '__main__':
    test_series = None
    do_test_only = False
    do_test_only = True
    if do_test_only:
        do_each_param = False
#        do_each_param = True
        if do_each_param:
            # do one of each parameter-code (but only one of multiple levels)
            test_series = csl.enumerate_all_results()
            test_series = [spec for spec in test_series
                           if spec[1] in (0.0, 850.0)]
            # filter to those after a current-problem one ...
            want_id_str = ''
#            want_id_str = '2d'
            i_interest = np.where(np.array(test_series)[:, 2] == want_id_str)
            i_interest = i_interest[0]
            if len(i_interest) > 0:
                test_series = test_series[i_interest:]
        else:
            # do one of each 'class' (of calculation we have to make)
            test_series = [
#                csl.pickout_spec(186),  # low-cloud (~"surface")
#                csl.pickout_spec(151),  # mslp
#                csl.pickout_spec(167),  # 2-metre temperature : gets height = 2.0m
#                csl.pickout_spec(165),  # 10-metre u-wind : gets height = 10.0m
#                csl.pickout_spec(166),  # 10-metre v-wind : gets height = 10.0m
#                csl.pickout_spec(157, 850),  # rh on p=850
## some odd extras..
##                csl.pickout_spec(141),  #  snow_depth
##                csl.pickout_spec(59),   # CAPE
##                csl.pickout_spec(168),   # dewpoint
                csl.pickout_spec(174),   # albedo

            ]

    main(series_specs=test_series,
#         load_from_cubes=False, save_as_cubes=True, save_as_grib=False
         load_from_cubes=True, save_as_cubes=False, save_as_grib=True
#         save_as_cubes=True
         )

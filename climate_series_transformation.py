'''
Created on Apr 17, 2013

@author: itpp

Grib climate-means project.
Code to load, aggregate and output grib climate data.

'''
import os.path

import iris.coord_categorisation

# local includes
import test_basic_load_and_timings as blt
import climate_series_loading as csl
from pp_utils import TimedBlock


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


default_output_dirpath = '/net/home/h05/itpp/Iris/climate_means/temp_outputs'

def main(output_dirpath=default_output_dirpath):
    series_specs = csl.enumerate_all_results()
    for param, level, target_id in series_specs:
        print '\nDoing : ', target_id
        print '  loading..'
        data_cube = csl.cube_for_param_and_level(param, level)
        print '  aggregating ..'
        data_cube = make_monthly_means_cube(data_cube)
        file_name = 'MonthlyMeans_{}.grib2'.format(target_id)
        file_path = os.path.join(output_dirpath, file_name)
        print '  saving to \'{}\' ...'.format(file_path)
        iris.save(data_cube, file_path)


if __name__ == '__main__':
    main()
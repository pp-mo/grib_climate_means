'''
Created on Apr 25, 2013

@author: itpp
'''

import datetime
import glob
import numpy as np
import os
import os.path
import pickle

import iris
import iris.fileformats.grib.grib_phenom_translation as g1_to_nc

# local modules
import grab_andys_file_summary as gafs
import test_basic_load_and_timings as blt

import climate_series_loading as csl
import climate_series_transformation as cst

default_output_dirpath = '/net/home/h05/itpp/Iris/climate_means/outputs'

def main(test_series, output_dirpath=default_output_dirpath):
    for param, level, target_id in test_series:
        g1_to_nc_data = g1_to_nc.grib1_phenom_to_cf_info(128, 98, int(param))
        name = g1_to_nc_data.standard_name or g1_to_nc_data.long_name
        print '\nDOING: "{}", standard_name = ({})'.format(target_id,  name)
        # load pickled version
        cubefile_name = 'MonthlyMeans_{}.cube.pkl'.format(target_id)
#        print '\nDoing : ', target_id
        file_path = os.path.join(output_dirpath, cubefile_name)
#        print '  loading cube from {} ..'.format(file_path)
        with open(file_path, 'r') as f:
            cube = pickle.load(f)
        print '  PICKLED cube short : ', cube.summary(shorten=True)
        print '      coords : ', [c.name() for c in cube.coords()]
        data_reduced = cube.data[np.where(np.abs(cube.data - 9999.0) > 1e-2)]
        print '      data range : ', (np.min(data_reduced), np.max(data_reduced))

        # load grib version
        name_stub = 'MonthlyMean_' + name
        if (float(level) != 0.0):
            name_stub += '_p{:.0f}'.format(float(level))
        height = g1_to_nc_data.set_height
        if height is not None and not np.isnan(height):
            name_stub += '_h{:.0f}'.format(float(height))
        name_stub += '.'
#        print '    (SEARCH: {})'.format(name_stub)
        grib_paths = glob.glob(output_dirpath+'/*.grib2')
        grib_paths = [l for l in grib_paths
                     if l.find(name_stub) >= 0]
        assert len(grib_paths) == 1
        grib_filepath = grib_paths[0]
        cube = iris.load_cube(grib_filepath)
        print '  GRIB cube short : ', cube.summary(shorten=True)
        print '      coords : ', [c.name() for c in cube.coords()]
        data_reduced = cube.data[np.where(np.abs(cube.data - 9999.0) > 1e-4)]
        print '      data range : ', (np.min(data_reduced), np.max(data_reduced))

#    print 'time ranges by month : '
#    co_t = cube.coord('time')
#    def show_month(i_month):
#        nums = co_t.bounds[i_month, :]
#        dates = [co_t.units.num2date(x) for x in nums]
#        print '  Jan : numbers {} : dates {}'.format(nums, dates)
#    show_month(0)
#    show_month(1)
#    print '    ...'
#    show_month(10)
#    show_month(11)


if __name__ == '__main__':
    do_all_types = True
    do_all_types = False
    if do_all_types:
        test_series = csl.enumerate_all_results()
        test_series = [spec for spec in test_series
                       if spec[1] in (0.0, 850.0)]
    else:
        test_series = [
            csl.pickout_spec(186),  # low-cloud (~"surface")
            csl.pickout_spec(151),  # mslp
            csl.pickout_spec(167),  # 2-metre temperature : gets height = 2.0m
            csl.pickout_spec(165),  # 10-metre u-wind : gets height = 10.0m
            csl.pickout_spec(166),  # 10-metre v-wind : gets height = 10.0m
            csl.pickout_spec(157, 850),  # rh on p=850
        ]
#        test_series = [csl.pickout_spec(186)]  # low cloud
#        test_series = [csl.pickout_spec(130, 850)]  # air temp

    main(test_series)

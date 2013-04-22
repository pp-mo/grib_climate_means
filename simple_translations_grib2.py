'''
Created on Apr 18, 2013

@author: itpp


Grib climate-means project.
Highly simplistic translation tables for GRIB1 input / GRIB2 output.

This to be replaced by more generic methods ASAP
(as is the )

'''
import numpy as np

import simple_translations_grib1 as stg1

class Grib2Code(object):
    names = ['name',
             'discipline', 'parameterCategory', 'parameterNumber',
             'units']

    def __init__(self, *args, **kwargs):
        for i_arg, arg in enumerate(args):
            kwargs[self.names[i_arg]] = arg
        for name in self.names:
            setattr(self, name, kwargs[name])

    def as_list(self):
        return [getattr(self, name) for name in self.names]

_GRIB2_NAME_TRANSLATIONS_LIST = []

def add_grib2_translation(*args, **kwargs):
    args = list(args)
    if args[0].startswith('__'):
        # reconstruct 'fudged' names
        args[0] = stg1.ECMWF_GRIB1_LOCALCODE_NAME_PREFIX + args[0]
    newcode = Grib2Code(*args, **kwargs)
    _GRIB2_NAME_TRANSLATIONS_LIST.append(newcode)

# Add all the codes we're interested in
add_grib2_translation('__low_cloud', 0, 6, 3, '%')
add_grib2_translation('__medium_cloud', 0, 6, 4, '%')
add_grib2_translation('__high_cloud', 0, 6, 5, '%')
add_grib2_translation('__total_cloud_cover', 0, 6, 1, '%')
add_grib2_translation('__snow_depth', 0, 1, 11, 'm')
add_grib2_translation('__mslp', 0, 3, 0, 'Pa')
add_grib2_translation('__10m_wind_x', 0, 2, 2, 'm s-1')
add_grib2_translation('__10m_wind_y', 0, 2, 3, 'm s-1')
add_grib2_translation('__2m_temp', 0, 0, 0, 'K')
add_grib2_translation('__2m_dewpoint', 0, 0, 6, 'K')

add_grib2_translation('__cape', 0, 7, 6, 'J Kg-1')
add_grib2_translation('__albedo', 0, 19, 1, '%')
add_grib2_translation('__sst', 10, 3, 0, 'K')
add_grib2_translation('__sea_ice_cover', 10, 2, 0, '1')
add_grib2_translation('__surface_roughness', 2, 0, 1, 'm')
  # LAND SURFACE discipline -is this right?
add_grib2_translation('__skin_temperature', 0, 0, 17, 'K')

add_grib2_translation('__relative_humidity', 0, 1, 1, '%')
add_grib2_translation('__temperature', 0, 0, 0, 'K')
add_grib2_translation('__geopotential', 0, 3, 4, 'm^2 s-2')
add_grib2_translation('__wind_u', 0, 2, 2, 'm s-1')
add_grib2_translation('__wind_v', 0, 2, 3, 'm s-1')
add_grib2_translation('__wind_z', 0, 2, 8, 'Pa s-1')  # a *pressure* velocity

# Convert to a recarray for easy searching.
# NOTE: failed to create by concatenation -- bugs in numpy
_GRIB2_CODES_ARRAY = np.core.records.fromrecords(
    [code.as_list() for code in _GRIB2_NAME_TRANSLATIONS_LIST],
    names=Grib2Code.names)


def identify_grib2_coding(name, debug=False):
    result_array = _GRIB2_CODES_ARRAY[
        np.where(_GRIB2_CODES_ARRAY.name == name)]
    n_results = len(result_array)
    if n_results > 1:
        raise ValueError('Grib2 lookup for name \'{}\' '
                         'found {} matches'.format(name, n_results))
    elif n_results == 1:
        result = result_array[0]
    else:
        # none found
        result = None
    if debug:
        r_str = str(result)
        print 'STG2-identify: name={} ==> {}'.format(name, r_str)
    return result


def test(debug=False):
    test_name = stg1.ECMWF_GRIB1_LOCALCODE_NAME_PREFIX + '__snow_depth'
    expected_results = {'discipline': 0,
                        'parameterCategory': 1,
                        'parameterNumber': 11,
                        'units': 'm'}
    testrec = identify_grib2_coding(test_name)
    assert testrec != None
    for key, expected in expected_results.iteritems():
        got = getattr(testrec, key)
        assert got == expected

    testrec = identify_grib2_coding('completely_made_up')
    assert testrec == None


if __name__ == '__main__':
    test(debug=True)
    print '..Done ok.'
    t_dbg = 0

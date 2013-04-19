'''
Created on Apr 18, 2013

@author: itpp


Grib climate-means project.
Highly simplistic translation tables for GRIB1 input / GRIB2 output.

This to be replaced by more generic methods ASAP
(as is the )

'''
import numpy as np

# The Grib1 edition, table2version and centrecode are diagnostic for the ones
# we want to translate here.
ECMWF_DEFAULT_GRIB1_EDITION = 1

GRIB1_TABLE2VERSIONS = {
    'non_local': 0,
    'ecmwf_local': 128,
}

GRIB1_CENTRECODES = {'ecmwf': 98}

#
# These probably don't belong here ?
#
##NOTE: these match terms in Andy's listfile -- see "grab_andys_file_summary.py"
#GRIB1_LEVELTYPES = {'surface': 1, 'isobaricInhPa': 100}

class Grib1Code(object):
    main_names = ['edition', 'table2version', 'centre', 'param', 'longname']
    optional_names = {'set_height': np.NaN}
    all_names = main_names + optional_names.keys()

    def __init__(self, **kwargs):
        for name, default in self.optional_names.iteritems():
            if name not in kwargs:
                kwargs[name] = default
        for name in self.all_names:
            setattr(self, name, kwargs[name])

    def as_list(self):
        return [getattr(self, name) for name in self.all_names]

ECMWF_GRIB1_LOCALCODE_NAME_PREFIX = 'ecmwf_grib1_local__'

class EcmwfLocalGrib1Code(Grib1Code):
    def __init__(self, param, longname,
                 edition=ECMWF_DEFAULT_GRIB1_EDITION,
                 table2version=GRIB1_TABLE2VERSIONS['ecmwf_local'],
                 centre=GRIB1_CENTRECODES['ecmwf'],
                 **kwargs
                 ):
        super(EcmwfLocalGrib1Code, self).__init__(
            param=param,
            longname=ECMWF_GRIB1_LOCALCODE_NAME_PREFIX + longname,
            edition=edition,
            table2version=table2version,
            centre=centre,
            **kwargs)

_GRIB1_CODE_TRANSLATIONS_LIST = []

def add_ec_grib1(*args, **kwargs):
    global _GRIB1_CODE_TRANSLATIONS_LIST
    newcode = EcmwfLocalGrib1Code(*args, **kwargs)
    _GRIB1_CODE_TRANSLATIONS_LIST.append(newcode)

# Add all the codes we're interested in
# Use the set_height key to interpret codes that imply an AGL height
add_ec_grib1(186, 'low_cloud')
add_ec_grib1(187, 'medium_cloud')
add_ec_grib1(187, 'high_cloud')
add_ec_grib1(164, 'total_cloud_cover')
add_ec_grib1(141, 'snow_depth')
add_ec_grib1(151, 'mslp')
add_ec_grib1(165, '10m_wind_x', set_height=10.0)
add_ec_grib1(166, '10m_wind_y', set_height=10.0)
add_ec_grib1(167, '2m_temp', set_height=2.0)
add_ec_grib1(168, '2m_dewpoint', set_height=2.0)

add_ec_grib1(59, 'cape')
add_ec_grib1(174, 'albedo')
add_ec_grib1(34, 'sst')
add_ec_grib1(31, 'sea_ice_cover')
add_ec_grib1(173, 'surface_roughness')
add_ec_grib1(235, 'skin_temperature')

add_ec_grib1(157, 'relative_humidity')
add_ec_grib1(130, 'temperature')
add_ec_grib1(129, 'geopotential')
add_ec_grib1(131, 'wind_u')
add_ec_grib1(132, 'wind_v')
add_ec_grib1(135, 'wind_z')

# Convert to a recarray for easy searching.
# NOTE: failed to create by concatenation -- bugs in numpy
_GRIB1_CODES_ARRAY = np.core.records.fromrecords(
    [code.as_list() for code in _GRIB1_CODE_TRANSLATIONS_LIST],
    names=Grib1Code.all_names)


def identify_grib1_key(edition, table2version, centre, param):
    result_array = _GRIB1_CODES_ARRAY[
        np.where(np.logical_and(
            _GRIB1_CODES_ARRAY.edition == edition,
            np.logical_and(
                _GRIB1_CODES_ARRAY.table2version == table2version,
                np.logical_and(_GRIB1_CODES_ARRAY.centre == centre,
                               _GRIB1_CODES_ARRAY.param == param))))]
    n_results = len(result_array)
    if n_results != 1:
        raise ValueError('Ecmwf grib1 lookup for param \'{:s}\' '
                         'found {:d} matches'.format(param, n_results))
    return result_array[0]

def test():
    test_param = 186
    test_name = ECMWF_GRIB1_LOCALCODE_NAME_PREFIX + 'low_cloud'
    testcode = EcmwfLocalGrib1Code(9999, '__junk__')
    testrec = identify_grib1_key(
        edition=ECMWF_DEFAULT_GRIB1_EDITION,
        table2version=GRIB1_TABLE2VERSIONS['ecmwf_local'],
        centre=GRIB1_CENTRECODES['ecmwf'],
        param=test_param)
    assert testrec.longname == test_name
    assert np.isnan(testrec.set_height)


#
# Now do similar to translate ECMWF local-table phenomena into GRIB2 codes.
#

if __name__ == '__main__':
    test()
    print '..Done ok.'
    t_dbg = 0

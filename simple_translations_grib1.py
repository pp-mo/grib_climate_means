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

# NOTE: this code already 'interpreted' by grib.py from a number to a string
GRIB1_CENTRECODES = {'ecmwf': 'ecmf'}

#
# These probably don't belong here ?
#
##NOTE: these match terms in Andy's listfile -- see "grab_andys_file_summary.py"
#GRIB1_LEVELTYPES = {'surface': 1, 'isobaricInhPa': 100}

class Grib1Code(object):
    main_names = ['edition', 'table2version', 'centre', 'param',
                  'longname', 'units']
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
    def __init__(self, param, longname, units,
                 edition=ECMWF_DEFAULT_GRIB1_EDITION,
                 table2version=GRIB1_TABLE2VERSIONS['ecmwf_local'],
                 centre=GRIB1_CENTRECODES['ecmwf'],
                 **kwargs
                 ):
        super(EcmwfLocalGrib1Code, self).__init__(
            param=param,
            longname=ECMWF_GRIB1_LOCALCODE_NAME_PREFIX + longname,
            units=units,
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
add_ec_grib1(186, 'low_cloud', '1')
add_ec_grib1(187, 'medium_cloud', '1')
add_ec_grib1(187, 'high_cloud', '1')
add_ec_grib1(164, 'total_cloud_cover', '1')
add_ec_grib1(141, 'snow_depth', 'm')
add_ec_grib1(151, 'mslp', 'hPa')
add_ec_grib1(165, '10m_wind_x', 'm s-1', set_height=10.0)
add_ec_grib1(166, '10m_wind_y', 'm s-1', set_height=10.0)
add_ec_grib1(167, '2m_temp', 'K', set_height=2.0)
add_ec_grib1(168, '2m_dewpoint', 'K', set_height=2.0)

add_ec_grib1(59, 'cape', 'J Kg-1')
add_ec_grib1(174, 'albedo', '1')
add_ec_grib1(34, 'sst', 'K')
add_ec_grib1(31, 'sea_ice_cover', '1')
add_ec_grib1(173, 'surface_roughness', 'm')
add_ec_grib1(235, 'skin_temperature', 'K')

add_ec_grib1(157, 'relative_humidity', '1')  # actually, this is %ge.  No unit
add_ec_grib1(130, 'temperature', 'K')
add_ec_grib1(129, 'geopotential', 'm^2 s-2')
add_ec_grib1(131, 'wind_u', 'm s-1')
add_ec_grib1(132, 'wind_v', 'm s-1')
add_ec_grib1(135, 'wind_z', 'm s-1')

# Convert to a recarray for easy searching.
# NOTE: failed to create by concatenation -- bugs in numpy
_GRIB1_CODES_ARRAY = np.core.records.fromrecords(
    [code.as_list() for code in _GRIB1_CODE_TRANSLATIONS_LIST],
    names=Grib1Code.all_names)


def identify_grib1_key(edition, table2version, centre, param, debug=False):
    result_array = _GRIB1_CODES_ARRAY[
        np.where(np.logical_and(
            _GRIB1_CODES_ARRAY.edition == edition,
            np.logical_and(
                _GRIB1_CODES_ARRAY.table2version == table2version,
                np.logical_and(_GRIB1_CODES_ARRAY.centre == centre,
                               _GRIB1_CODES_ARRAY.param == param))))]
    n_results = len(result_array)
    if n_results > 1:
        raise ValueError('Ecmwf grib1 lookup for param \'{:s}\' '
                         'found {:d} matches'.format(param, n_results))
    elif n_results == 1:
        result = result_array[0]
    else:
        # none found
        result = None
    if debug:
        r_str = str(result)
        print 'STG1-identify: edition={} t2v={} centre={}, param={} ==> {:s}'.format(
            edition, table2version, centre, param, r_str)
    return result


def test(debug=False):
    test_param = 141
    expected_name = ECMWF_GRIB1_LOCALCODE_NAME_PREFIX + 'snow_depth'
    expected_units = 'm'
    testrec = identify_grib1_key(
        edition=ECMWF_DEFAULT_GRIB1_EDITION,
        table2version=GRIB1_TABLE2VERSIONS['ecmwf_local'],
        centre=GRIB1_CENTRECODES['ecmwf'],
        param=test_param,
        debug=debug)
    assert testrec != None
    assert testrec.longname == expected_name
    assert testrec.units == expected_units
    assert np.isnan(testrec.set_height)


if __name__ == '__main__':
    test(debug=True)
    print '..Done ok.'
    t_dbg = 0

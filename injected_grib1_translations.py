'''
Created on Apr 18, 2013

@author: itpp


Grib climate-means project.
Hacked version of 'simple_translations_grib1', to use "real" metadata info
 (from MH metadata engine)

'''
import numpy as np

import grib_cf_map as grcf

# The Grib1 edition, table2version and centrecode are diagnostic for the ones
# we want to translate here.
ECMWF_DEFAULT_GRIB1_EDITION = 1

GRIB1_TABLE2VERSIONS = {
    'non_local': 0,
    'ecmwf_local': 128,
}

# NOTE: this code already 'interpreted' by grib.py from a number to a string
GRIB1_CENTRECODES = {'ecmwf': 'ecmf',
                     98: 'ecmf'
                    }

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

class EcmwfLocalGrib1Code(Grib1Code):
    def __init__(self, param, longname, units,
                 edition=ECMWF_DEFAULT_GRIB1_EDITION,
                 table2version=GRIB1_TABLE2VERSIONS['ecmwf_local'],
                 centre=GRIB1_CENTRECODES['ecmwf'],
                 **kwargs
                 ):
        super(EcmwfLocalGrib1Code, self).__init__(
            param=param,
            longname=longname,
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

# FOR NOW: cludge the set_height info for the few params it affects...
def _ecmwf_local_grib1data_key(param, edition=1, t2version=128, centre=98):
    """
    Construct 'grib_cf_map' compliant key for ECMWF local param type.

    NOTE: at present contains "magic" numbers, as grib_cf_map does not export
    the constants we need to implement ecmwf-local-table

    """
    return grcf.G1Lparam(
                         edition=edition,
                         t2version=t2version,
                         centre=centre,
                         iParam=param)

_GRIB1_CODE_IMPLIED_LEVELS = {
    _ecmwf_local_grib1data_key(165): 10.0,  # 10m wind x
    _ecmwf_local_grib1data_key(166): 10.0,  # 10m wind y
    _ecmwf_local_grib1data_key(167): 10.0,  # 2m temp
    _ecmwf_local_grib1data_key(168): 2.0,  # 2m dewpoint
}

# interpret whole of imported Grib1-to-CF table into our own format
for (grib1data, cfdata) in grcf.GRIB1Local_TO_CF.iteritems():
    units_as_string = str(cfdata.unit)
    centre_as_string = GRIB1_CENTRECODES[grib1data.centre]
    set_height = _GRIB1_CODE_IMPLIED_LEVELS.get(
        _ecmwf_local_grib1data_key(param=grib1data.iParam,
                                   edition=grib1data.edition,
                                   t2version=grib1data.t2version,
                                   centre=grib1data.centre,
                                   ),
        np.NaN)
    add_ec_grib1(
        param=grib1data.iParam,
        longname=cfdata.standard_name or cfdata.long_name,
        units=units_as_string,
        edition=grib1data.edition,
        table2version=grib1data.t2version,
        centre=centre_as_string,
        set_height=set_height
        )

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
        raise ValueError('Ecmwf grib1 lookup for param \'{}\' '
                         'found {} matches'.format(param, n_results))
    elif n_results == 1:
        result = result_array[0]
    else:
        # none found
        result = None
    if debug:
        r_str = str(result)
        print 'STG1-identify: edition={} t2v={} centre={}, param={} ==> {}'.format(
            edition, table2version, centre, param, r_str)
    return result


def identify_known_ecmwf_key(param, debug=False):
    return identify_grib1_key(
        edition=ECMWF_DEFAULT_GRIB1_EDITION,
        table2version=GRIB1_TABLE2VERSIONS['ecmwf_local'],
        centre=GRIB1_CENTRECODES['ecmwf'],
        param=param, debug=debug)


def test(debug=False):
    test_param = 164
    expected_name = 'cloud_area_fraction'
    expected_units = '1'
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

    # Test ecmwf-specific call version
    testrec2 = identify_known_ecmwf_key(test_param, debug=True)
    assert testrec2 != None
    assert testrec.longname == expected_name
    assert testrec.units == expected_units
    assert np.isnan(testrec.set_height)
    # NOTE: *another* recarrary anomaly -- why does this not work ???
#    assert testrec2 == testrec

    # Test implied-level case
    test_param = 165
    expected_name = '10_metre_wind_x'
    expected_units = 'm s-1'
    testrec = identify_grib1_key(
        edition=ECMWF_DEFAULT_GRIB1_EDITION,
        table2version=GRIB1_TABLE2VERSIONS['ecmwf_local'],
        centre=GRIB1_CENTRECODES['ecmwf'],
        param=test_param,
        debug=debug)
    assert testrec != None
    assert testrec.longname == expected_name
    assert testrec.units == expected_units
    assert testrec.set_height == 10.0

    # test non-found one
    test_param = 999
    testrec = identify_known_ecmwf_key(test_param, debug=True)
    assert testrec is None

    #
    # rest not yet functional ...
    #
#        # test a set-height case
#        add_ec_grib1(168, '__2m_dewpoint', 'K', set_height=2.0)
#        test_param = 168  # 2m_dewpoint
#        expected_name = ECMWF_GRIB1_LOCALCODE_NAME_PREFIX + '__2m_dewpoint'
#        expected_units = 'K'
#        expected_height = 2.0
#        testrec = identify_known_ecmwf_key(test_param, debug=True)
#        assert testrec != None
#        assert testrec.longname == expected_name
#        assert testrec.units == expected_units
#        assert not np.isnan(testrec.set_height)
#        assert testrec.set_height == expected_height

if __name__ == '__main__':
    test(debug=True)
    print '..Done ok.'
    t_dbg = 0

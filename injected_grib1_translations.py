'''
Created on Apr 18, 2013

@author: itpp


Grib climate-means project.
Hacked version of 'simple_translations_grib1', to use "real" metadata info
 (from MH metadata engine)

'''
import warnings

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
                     98: 'ecmf',
                     }


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
    return grcf.G1Lparam(edition=edition,
                         t2version=t2version,
                         centre=centre,
                         iParam=param)


_GRIB1_CODE_IMPLIED_LEVELS = {
    _ecmwf_local_grib1data_key(165): 10.0,  # 10m wind x
    _ecmwf_local_grib1data_key(166): 10.0,  # 10m wind y
    _ecmwf_local_grib1data_key(167): 10.0,  # 2m temp
    _ecmwf_local_grib1data_key(168): 2.0,  # 2m dewpoint
}


def _install_grib_cf_lookup(grib1data, cfdata, implied_dimcoord=None):
    units_as_string = str(cfdata.unit)
    centre_as_string = GRIB1_CENTRECODES[grib1data.centre]
    set_height = np.NAN
    if implied_dimcoord is not None:
        err_prefix = ('Problem handling Grib1 conversion '
                      + 'with implied coordinate {} :\n'.format(
                          str(extra_dimcoord)))
        if implied_dimcoord.standard_name != 'height':
            warnings.warn(err_prefix +
                          'Coordinate standard_name is "{}", but currently '
                          'only recognise "height": Ignoring.'.format(
                              implied_dimcoord.standard_name))
        else:
            if implied_dimcoord.units != 'm':
                raise ValueError(err_prefix +
                                 'Coordinate units is "{}", but can only '
                                 'handle metres at present.'.format(
                                     implied_dimcoord.units))
            if len(implied_dimcoord.points) != 1:
                raise ValueError(err_prefix +
                                 'Coordinate has multiple points : {}\n'
                                 'Only one point is currently '
                                 'supported.'.format(
                                     implied_dimcoord.points))
            set_height = implied_dimcoord.points[0]
    add_ec_grib1(param=grib1data.iParam,
                 longname=cfdata.standard_name or cfdata.long_name,
                 units=units_as_string,
                 edition=grib1data.edition,
                 table2version=grib1data.t2version,
                 centre=centre_as_string,
                 set_height=set_height)


# Interpret whole of imported Grib1-to-CF table into our own format
for (grib1data, cfdata) in grcf.GRIB1Local_TO_CF.iteritems():
    _install_grib_cf_lookup(grib1data, cfdata)

# Do the same for the special table specifying Grib1-to-CF with implied levels
for (grib1data, (cfdata, extra_dimcoord)) \
        in grcf.GRIB1LocalConstrained_TO_CF.iteritems():
    _install_grib_cf_lookup(grib1data, cfdata, extra_dimcoord)

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
        print 'STG1-identify: edition={} t2v={} centre={}, param={} '
        '==> {}'.format(
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
    assert testrec is not None
    assert testrec.longname == expected_name
    assert testrec.units == expected_units
    assert np.isnan(testrec.set_height)

    # Test ecmwf-specific call version
    testrec2 = identify_known_ecmwf_key(test_param, debug=True)
    assert testrec2 is not None
    assert testrec.longname == expected_name
    assert testrec.units == expected_units
    assert np.isnan(testrec.set_height)
    # NOTE: *another* recarrary anomaly -- why does this not work ???
#    assert testrec2 == testrec

    # Test implied-level case
    test_param = 165
    expected_name = 'x_wind'
    expected_units = 'm s-1'
    testrec = identify_grib1_key(
        edition=ECMWF_DEFAULT_GRIB1_EDITION,
        table2version=GRIB1_TABLE2VERSIONS['ecmwf_local'],
        centre=GRIB1_CENTRECODES['ecmwf'],
        param=test_param,
        debug=debug)
    assert testrec is not None
    assert testrec.longname == expected_name
    assert testrec.units == expected_units
    assert testrec.set_height == 10.0

    # test non-found one
    test_param = 999
    testrec = identify_known_ecmwf_key(test_param, debug=True)
    assert testrec is None

    # Test error traps
    def _testerr(call_fn, expect_err_str=None, no_catch=False, debug=False):
        if no_catch:
            call_fn()
            if debug:
                print 'TEST invocation succeeded.'
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                call_fn()
            e = None
        except Exception as e1:
            e = e1
        print 'TEST exception caught : ', e
        if expect_err_str is '':
            if e is None:
                if debug:
                    print 'TEST not failed -- as expected.'
            else:
                raise Exception('ERROR: test failed unexpectedly.')
        elif expect_err_str is None:
            if e is not None:
                if debug:
                    print 'TEST failed -- as expected.'
            else:
                raise Exception('ERROR: test succeeded unexpectedly.')
        else:
            if str(e) == expect_err_str:
                if debug:
                    print 'TEST failed with expected error.'
            else:
                raise Exception('ERROR: test succeeded unexpectedly.')

    def _t1():
        _install_grib_cf_lookup(grib1data=grcf.G1Lparam(1, 128, 98, 165),
                                cfdata=grcf.CFname("x_wind", None, "m s-1"),
                                implied_dimcoord=grcf.DimensionCoordinate(
                                    "height", "m", (10,)))

    _testerr(_t1, '')

    def _t2():
        _install_grib_cf_lookup(grib1data=grcf.G1Lparam(1, 128, 98, 165),
                                cfdata=grcf.CFname("x_wind", None, "m s-1"),
                                implied_dimcoord=grcf.DimensionCoordinate(
                                    "pressure", "hPa", (10,)))

    _testerr(_t2)

    def _t3():
        _install_grib_cf_lookup(grib1data=grcf.G1Lparam(1, 128, 98, 165),
                                cfdata=grcf.CFname("x_wind", None, "m s-1"),
                                implied_dimcoord=grcf.DimensionCoordinate(
                                    "height", "ft", (10,)))

    _testerr(_t3)

    def _t4():
        _install_grib_cf_lookup(grib1data=grcf.G1Lparam(1, 128, 98, 165),
                                cfdata=grcf.CFname("x_wind", None, "m s-1"),
                                implied_dimcoord=grcf.DimensionCoordinate(
                                    "height", "m", (10, 20,)))

    _testerr(_t4)


if __name__ == '__main__':
    test(debug=True)
    print '..Done ok.'
    t_dbg = 0

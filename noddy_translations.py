'''
Created on Apr 18, 2013

@author: itpp


Grib climate-means project.
Highly simplistic translation tables for GRIB1 input / GRIB2 output.

This to be replaced by more generic methods ASAP
(as is the )

'''
import numpy as np

GRIB1_TABLE2VERSIONS = {
    'non_local': 0,
    'ecmwf_local': 128,
}

GRIB1_CENTRECODES = {'ecmwf': 98}

#NOTE: these match terms in Andy's listfile -- see "grab_andys_file_summary.py"
GRIB1_LEVELTYPES = {'surface': 1, 'isobaricInhPa': 100}

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


class EcmwfLocalGrib1Code(Grib1Code):
    _ecg1 = 'ecmwf_grib1_local__'
    def __init__(self, param, longname,
                 edition=1,
                 table2version=GRIB1_TABLE2VERSIONS['ecmwf_local'],
                 centre=GRIB1_CENTRECODES['ecmwf'],
                 **kwargs
                 ):
        super(EcmwfLocalGrib1Code, self).__init__(
            param=param,
            longname=self._ecg1 + longname,
            edition=edition,
            table2version=table2version,
            centre=centre,
            **kwargs)

GRIB1_CODE_TRANSLATIONS = []

def add_ec_grib1(*args, **kwargs):
    global GRIB1_CODE_TRANSLATIONS
    newcode = EcmwfLocalGrib1Code(*args, **kwargs)
    GRIB1_CODE_TRANSLATIONS.append(newcode)

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

GRIB1_CODES_ARRAY = np.core.records.fromrecords(
    [code.as_list() for code in GRIB1_CODE_TRANSLATIONS],
    names=Grib1Code.all_names)

t_dbg =0

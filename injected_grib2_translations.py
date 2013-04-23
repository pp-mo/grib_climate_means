'''
Created on Apr 18, 2013

@author: itpp


Grib climate-means project.
Hacked version of 'simple_translations_grib2', to use "real" metadata info
 (from MH metadata engine)

'''
import numpy as np

import grib_cf_map as grcf

import injected_grib1_translations as grib1_translate

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
    newcode = Grib2Code(*args, **kwargs)
    _GRIB2_NAME_TRANSLATIONS_LIST.append(newcode)

# interpret whole of imported CF-to-Grib2 table into our own format
for cf_data, grib2_data in grcf.CF_TO_GRIB2.iteritems():
    # NOTE: for now, continue blurred difference between standard+long names
    if grib2_data.edition == 2:
        name = cf_data.standard_name or cf_data.long_name
        add_grib2_translation(
            discipline=grib2_data.discipline,
            parameterCategory=grib2_data.category,
            parameterNumber=grib2_data.number,
            name=name,
            units=cf_data.unit
            )

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
    test_name = 'air_potential_temperature'
    expected_results = {'discipline': 0,
                        'parameterCategory': 0,
                        'parameterNumber': 2,
                        'units': 'K'}
    testrec = identify_grib2_coding(test_name, debug=True)
    assert testrec != None
    for key, expected in expected_results.iteritems():
        got = getattr(testrec, key)
        assert got == expected, "value for {} expected={} got={}".format(
            key, expected, got)

    # test a missing one
    testrec = identify_grib2_coding('completely_made_up', debug=True)
    assert testrec == None


if __name__ == '__main__':
    test(debug=True)
    print '..Done ok.'
    t_dbg = 0

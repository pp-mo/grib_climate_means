'''
Created on Apr 23, 2013

@author: itpp
'''
# control between imported and local grib1/2 metadata translation information
use_imported_grib_to_cf_translations = True
#use_imported_grib_to_cf_translations = True

if use_imported_grib_to_cf_translations:
    import injected_grib1_translations as grib1_translate
    import injected_grib2_translations as grib2_translate
else:
    import simple_translations_grib1 as grib1_translate
    import simple_translations_grib2 as grib2_translate

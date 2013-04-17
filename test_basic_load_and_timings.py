'''
Created on Apr 15, 2013

@author: itpp

Test loading and load-times on ERA cliimate-data gribfiles.

'''

import datetime
import glob
import os
import os.path


import iris
import iris.exceptions
import iris.coord_categorisation
import iris.analysis

from pp_utils import TimedBlock

climdir_spec=['/', 'project', 'avd', 'means', 'input']
climdir_path = os.path.join(*climdir_spec)
filenames_spec = '*.gr*'
filenames_pathspec = os.path.join(climdir_path, filenames_spec)
#print 'searching: ',filenames_pathspec
climate_file_paths = glob.glob(filenames_pathspec)

# Choose the SMALLEST to be going on with (!)
testfile_name = 'batch-mars-web238-20130327141600-S5u9ru.grib'
testfile_path = os.path.join(climdir_path, testfile_name)
#print 'FIRST FILE : ', testfile_path

def phenom_callback(cube, field, filename):
    # start with low cloud cover
    if field.indicatorOfParameter==186:
        cube.rename('Low cloud cover')
        # set level aux coords scalar coord for 167/168
    else:
        raise iris.exceptions.IgnoreCubeException

def timeit(*args, **kwargs):
    with TimedBlock() as t:
        cubes = iris.load(*args, **kwargs)
    print '\nTime taken ({!r}):\n = {:0.2f}'.format((args, kwargs), t.seconds())
    return cubes, t

def timeit_raw(*args, **kwargs):
    print '\nTIMEIT-RAW {!r}'.format((args, kwargs))
    with TimedBlock() as t:
        cubes = iris.load_raw(*args, **kwargs)
    print '\nTime taken {!r}:\n = {:0.2f}'.format((args, kwargs), t.seconds())
    return cubes, t

mb = 1024.0 ** 2
pmb = 1.0 /mb

def testit(filepath, timefn=timeit):
    print '\nFILE : ', filepath
    nbytes = os.path.getsize(filepath)
    print '  size = {:.1f} Mb'.format(nbytes * pmb)
    cubes,_ = timefn(filepath)
    print 'N-cubes = ', len(cubes)
    print 'cubes[0]...'
    print cubes[0]


if __name__ == '__main__':
    testit(testfile_path, timefn=timeit_raw)


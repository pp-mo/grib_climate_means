'''
Created on Apr 16, 2013

@author: itpp

Grib climate-means project.
Process filelist.lis into database of per-grib-message information.

'''
import numpy as np
import os.path

class bufferline(object):
    def __init__(self, file):
        self.file = file
        self.has_more = True
        # initialise with first line
        self._current_line = None
        self.take()

    def peek(self):
        return self._current_line

    def take(self):
        result = self._current_line
        self._current_line = None
        try:
            self._current_line = self.file.readline().strip()
        except StopIteration:
            self.has_more = False
        return result

def read_andys_listfile_datastrings(file):
    i_file = 0
    data = []
    columns = ['i_file', 'filename']
    rdr = bufferline(file)
    counts_line_signature = 'grib messages in'
    while rdr.has_more:
        filename = rdr.take()
        if filename.find(counts_line_signature) >= 0:
            # last summary line looks like a file summary, signals end
            break
        if i_file == 0:
            # keyline just after the FIRST filename only
            columns += rdr.take().split()
        dataline_prefix = [str(i_file), filename]
#        print 'Starting : ', dataline_prefix
        while rdr.peek().find(counts_line_signature) < 0:
            dataline = dataline_prefix + rdr.take().split()
            data.append(dataline)
        # at end of eack file summary, expect :
        #   - a counts message "NNN of NNN grib messages in FFFF"
        #   - a blank line [[ALLOW SEVERAL..]]
        assert rdr.take().find(counts_line_signature)
        while rdr.has_more and len(rdr.peek()) == 0:
            rdr.take()
        # bump filenumber
        i_file += 1

    return data, columns

def gribmsg_data_as_recarray(listfile_path):
    with open(listfile_path) as f:
        data_strings, column_names = read_andys_listfile_datastrings(f)
    records = np.core.records.fromrecords(data_strings,
                                          names=column_names)
    return records

# Original location
#_climate_dir_spec = ['/', 'project', 'avd', 'means']
#_summary_location_spec = ['example_messages']
#default_summary_dirspec = _climate_dir_spec + _summary_location_spec
default_summary_dirspec = ['/', 'home', 'h05', 'itpp', 'Iris',
                           'climate_means', 'message_info_backup']
default_summary_file_name = 'file_list.lis'
default_summary_file_spec = default_summary_dirspec + [default_summary_file_name]
default_summary_file_path = os.path.join(*default_summary_file_spec)

def print_summary():
    data_recs = gribmsg_data_as_recarray(default_summary_file_path)

    shortnames = set(data_recs.shortName)
    data_bynames = {shortname: data_recs[np.where(data_recs.shortName == shortname)]
                    for shortname in shortnames}
    key_names = set(data_recs.dtype.names)
    # these keys take only one value
    omit_keys = set(['packingType', 'gridType', 'centre', 'edition'])
    for keyname in omit_keys:
        assert len(set(getattr(data_recs, keyname))) == 1
    # these keys are just not wanted in printout
    omit_extra_keys = set(['filename', 'shortName', 'dataDate'])
    omit_keys |= omit_extra_keys
    wanted_keys = sorted(key_names - omit_keys)
    print 'Key values ...'
    for keyname in wanted_keys:
        values = sorted(set(getattr(data_recs, keyname)))
        print '  {} values : {}'.format(keyname, values)
    print '\nBreakdown by shortnames ...'
    for shortname in shortnames:
        print "\nFOR '{}'".format(shortname)
        n_msgs = len(data_bynames[shortname])
        n_levels = len(set(data_bynames[shortname].level))
        n_mpl = float(n_msgs)/n_levels
        assert( abs(n_mpl - 360.0) < 0.01 )
#        print "  n-msgs = ", n_msgs
#        print "  n-msgs/lev = ", n_mpl
        for keyname in wanted_keys:
            key_values = sorted(set(getattr(data_bynames[shortname], keyname)))
            print "  {key} values : {set}".format(key=keyname,
                                                  set=key_values)

if __name__ == '__main__':
    print_summary()
    t_dbg = 0

import os
import re
import numpy as np
from collections import OrderedDict
from oceanwaves import OceanWaves


class XBeachModel(OrderedDict):


    def __init__(self, **kwargs):
        super(XBeachModel, self).__init__()
        self['_params'] = XBeachParams(**kwargs)


    def __repr__(self):
        s = 'XBeach Model Object:\n\n'
        for name, obj in self.iteritems():
            if not name.startswith('_'):
                s += '  %s:\n' % name
            s += obj.pretty_print(indent=4)
            s += '\n'
        return s
    

    def set_bathymetry(self, *args, **kwargs):
        self['bathymetry'] = XBeachBathymetry(*args, **kwargs)

        
    def set_waves(self, *args, **kwargs):
        self['waves'] = XBeachWaves(*args, **kwargs)


    def read(self, fpath):
        pass

    
    def write(self, fpath):
        if not os.path.exists(fpath):
            os.makedirs(fpath)
        params = XBeachParams(self['_params'])
        for name, obj in self.iteritems():
            obj.write(fpath)
            params.update(obj)
        params.write(fpath)


    def run(self):
        pass


class XBeachParams(OrderedDict):


    _fmt = '%-10s = %s\n'
    _desc = 'XBeach Params Object'
    _file = 'params.txt'
    
    
    def __repr__(self):
        s = '%s:\n\n' % self._desc
        s += self.pretty_print(indent=2)
        return s

    
    def read(self, fname):
        pass


    def write(self, fpath):
        with open(os.path.join(fpath, self._file), 'w') as fp:
            fp.write(self.pretty_print())


    def pretty_print(self, indent=0):
        s = ''
        for k, v in self.iteritems():
            s += (' ' * indent) + self._fmt % (k, self.pretty_print_value(v))
        return s
            
        
    def pretty_print_value(self, v):
        if type(v) is list:
            return ' '.join([self.pretty_print_value(vi) for vi in v])
        elif type(v) is str:
            return v
        elif type(v) is int:
            return '%d' % v
        elif type(v) is float:
            return '%0.4f' % v
        elif type(v) is bool:
            return '%d' % v
        else:
            return str(v)


    @staticmethod
    def enumerate_filename(fname, i):
        fname, fext = os.path.splitext(fname)
        return '%s_%03d%s' % (fname, i, fext)


class XBeachBathymetry(XBeachParams):


    x = None
    y = None
    z = None
    
    _desc = 'XBeach Bathymetry Object'
    _file = None
    _filex = 'x.txt'
    _filey = 'y.txt'
    _filez = 'z.txt'
                

    def __init__(self, *args, **kwargs):
        super(XBeachBathymetry, self).__init__(**kwargs)

        if len(args) == 2:

            self.x = np.asarray(args[0]).reshape((1,-1))
            self.z = np.asarray(args[1]).reshape((1,-1))
            
            self['ny'] = 0
            
        elif len(args) == 3:

            self.y = np.asarray(args[1])
            self.z = np.asarray(args[2])
            
            self['ny'] = self.y.shape[0] - 1
            self['yfile'] = self._filey
            
        else:
            raise ValueError('Expected 2 or 3 non-keyword arguments, got %d', len(args))

        self['nx'] = self.x.shape[1] - 1
        self['xfile'] = self._filex
        self['depfile'] = self._filez


    def write(self, fpath):
        np.savetxt(os.path.join(fpath, self['xfile']), self.x)
        np.savetxt(os.path.join(fpath, self['depfile']), self.z)

        if self.y is not None:
            np.savetxt(os.path.join(fpath, self['yfile']), self.y)


class XBeachWaves(XBeachParams):


    _desc = 'XBeach Waves Object'
    _file = 'waves.txt'
    _filetime = 'filelist.txt'
    _fileloc = 'loclist.txt'
    _filespc = 'waves.SP2'

    rt = 1.
    
    
    def __init__(self, *args, **kwargs):

        self._ow = OceanWaves(*args, **kwargs)

        super(XBeachWaves, self).__init__()

        if self._ow.has_dimension('time'):
            self['bcfile'] = self._filetime
        elif self._ow.has_dimension('location'):
            self['bcfile'] = self._fileloc
        elif self._ow.has_dimension('frequency'):
            self['bcfile'] = self._filespc
        else:
            self['bcfile'] = self._file

        if self._ow.has_dimension('frequency'):
            self['instat'] = 'swan'
        else:
            self['instat'] = 'jons'


    def write(self, fpath):

        if self._ow.has_dimension('frequency'):
            self._ow.to_swan(os.path.join(fpath, self._filespc))
        else:
            self.write_jonswap(fpath)
            
        if self._ow.has_dimension('time'):
            self.write_filelist(fpath)
        elif self._ow.has_dimension('location'):
            self.write_loclist(fpath)


    def write_jonswap(self, fpath):
        for i, ow in enumerate(self._ow.iterdim('_time')):
            if self._ow.has_dimension('time'):
                fname = self.enumerate_filename(self._file, i)
            else:
                fname = self._file
            with open(os.path.join(fpath, fname), 'w') as fp:
                fp.write('Hm0 = %0.6f\n' % ow['_energy'].values)
                fp.write('Tp = %0.6f\n' % 12.) # FIXME: this should be fixed in oceanwaves (1./ow['_frequency'].values)
                fp.write('mainang = %0.6f\n' % 0.) # FIXME: this should be fixed in oceanwaves (ow['_direction'].values)
                fp.write('gammajsp = 3.3\n')
                fp.write('s = 10.\n')
                fp.write('fnyq = 0.3\n')
    

    def write_filelist(self, fpath):
        with open(os.path.join(fpath, self._filetime), 'w') as fp:
            fp.write('FILELIST\n')
            for i, t in enumerate(self._ow['_time']):
                if self._ow.has_dimension('location'):
                    fname = self.enumerate_filename(self._fileloc, i)
                    self.write_loclist(fpath)
                elif self._ow.has_dimension('frequency'):
                    fname = self.enumerate_filename(self._filespc, i)
                else:
                    fname = self.enumerate_filename(self._file, i)
                fp.write('%10.4f %10.4f %s\n' % (t, self.rt, fname))


    def write_loclist(self, fpath):
        with open(os.path.join(fpath, self._fileloc), 'w') as fp:
            fp.write('LOCLIST\n')
            for i, l in enumerate(self._ow['_location']):
                if self._ow.has_dimension('frequency'):
                    fname = self.enumerate_filename(self._filespc, i)
                else:
                    fname = self.enumerate_filename(self._file, i)
                x = self._ow['x'][i]
                y = self._ow['y'][i]
                fp.write('%10.4f %10.4f %s\n' % (x, y, fname))

            
class XBeachWaterlevel(XBeachParams):

    
    def __init__(self):
        pass


class XBeachVegetation(XBeachParams):

    
    def __init__(self):
        pass


class XBeachShips(XBeachParams):

    
    def __init__(self):
        pass

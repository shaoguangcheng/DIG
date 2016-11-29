# Author: Shaoguang Cheng
# Date: 2016.11.29

import numpy as np
from tempfile import mkdtemp
from DIG.externals.joblib import Memory

cachedir = mkdtemp()
memory = Memory(cachedir=cachedir, verbose=0)

# store at disk
@memory.cache
def f(x):
    print('Runing f(%s)' % x)
    return x


# To speed up cache looking of large numpy arrays, you can load them using memmapping (memory mapping)
cachedir2 = mkdtemp()
memory2 = Memory(cachedir=cachedir2, mmap_mode='r')

@memory2.cache
def g(x):
    print('Runing g(%s)' % x)
    return np.square(x)

if __name__ == '__main__':
    f(1)
    f(1)

    print(g([1,2,3]))
    print(g([1,2,3]))

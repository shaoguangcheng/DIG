# Author: Shaoguang Cheng
# Date: 2016.11.29

from DIG.externals.joblib import Parallel, delayed
from math import sqrt

def parallel_test1():
    array = Parallel(n_jobs=100, backend='multiprocessing')(delayed(sqrt)(i ** 2) for i in range(10))
    print array


# Calling Parallel several times in a loop is sub-optimal because it will create and destroy a pool of workers (threads or processes) several times which can cause a significant overhead.
# For this case it is more efficient to use the context manager API of the Parallel class to re-use the same pool of workers for several calls to the Parallel object
# http://www.tuicool.com/articles/7zIra2r
def parallel_test2():
    with Parallel(n_jobs=2) as parallel:
        accumulator = 0.
        n_iter = 0
        while accumulator < 1:
            results = parallel(delayed(sqrt)(accumulator + i ** 2)
                               for i in range(5))
            accumulator += sum(results)  # synchronization barrier
        n_iter += 1

        print(accumulator, n_iter)
    return  accumulator


if __name__ == '__main__':
    parallel_test1()
    parallel_test2()
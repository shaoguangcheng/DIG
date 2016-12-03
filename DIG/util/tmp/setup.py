#encoding:utf-8

from distutils.core import setup,Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext
import numpy as np
#cythonize：编译源代码为C或C++，返回一个distutils Extension对象列表

#setup(
#    ext_modules=[
#        Extension("_logistic_sigmoid", ["_logistic_sigmoid.c"],
#                  include_dirs=[np.get_include()]),
#    ],
#)

setup(
	include_dirs = [np.get_include()],
	ext_modules=cythonize('_logistic_sigmoid.pyx')
	)
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("chronosmatch.engine.order_book",
              ["chronosmatch/engine/order_book.pyx"])
]

setup(
    name="chronosmatch",
    version="0.1.0",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
    ),
)

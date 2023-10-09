from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

ext_modules = [
    Extension("csv_helper", ["helpers/csv_helper.py"]),
    Extension("scraper", ["helpers/scraper.py"]),
    Extension("listing_helper", ["helpers/listing_helper.py"]),
    Extension("history", ["helpers/history.py"]),
    Extension("app", ["app.py"])

]
setup(
    name = 'Facebook Marketplace Bot',
    cmdclass = {'build_ext': build_ext},
    ext_modules = cythonize(ext_modules),
    compiler_directives={'language_level': 3},
    zip_safe=False
)

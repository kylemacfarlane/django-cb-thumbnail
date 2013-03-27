import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'django-cuddlybuddly-thumbnail',
    version = '2.6',
    license = 'BSD',
    description = 'A Django app that supplies a template tag to generate ' \
                  'thumbnails. Specifically designed to be compatible with ' \
                  'properly implemented Django storage systems, which ' \
                  'unfortunately most are not.',
    long_description = read('README.rst'),
    author = 'Kyle MacFarlane',
    author_email = 'kyle@deletethetrees.com',

    package_dir = {'': 'src'},
    packages = find_packages('src'),
    namespace_packages = ['cuddlybuddly'],
    include_package_data = True,
    zip_safe = False,

    install_requires = ['setuptools'],

    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP'
    ],
)

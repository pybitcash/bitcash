from setuptools import find_packages, setup

with open('bitcash/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.strip().split('= ')[1].strip("'")
            break

setup(
    name='bitcash',
    version=version,
    description='BitcoinCash made easy.',
    long_description=open('README.rst', 'r').read(),
    author='Teran McKinney',
    author_email='sega01@go-beyond.org',
    maintainer='Teran McKinney',
    maintainer_email='sega01@go-beyond.org',
    url='https://github.com/teran-mckinney/bitcash',
    download_url='https://github.com/teran-mckinney/bitcash',
    license='MIT',

    keywords=(
        'bitcoincash',
        'cryptocurrency',
        'payments',
        'tools',
        'wallet',
    ),

    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ),

    install_requires=('coincurve>=4.3.0', 'requests'),
    extras_require={
        'cli': ('appdirs', 'click', 'privy', 'tinydb'),
        'cache': ('lmdb', ),
    },
    tests_require=['pytest'],

    packages=find_packages(),
    entry_points={
        'console_scripts': (
            'bitcash = bitcash.cli:bitcash',
        ),
    },
)

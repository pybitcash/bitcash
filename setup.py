from setuptools import find_packages, setup

with open('bitcash/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.strip().split('= ')[1].strip("'")
            break

try:
    long_description = open('README.md', 'r').read()
except Exception:
    long_description = 'Bitcoin Cash... failed to read README.md'

setup(
    name='bitcash',
    version=version,
    description='Bitcoin Cash made easier.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Teran McKinney',
    author_email='sega01@go-beyond.org',
    maintainer='Teran McKinney',
    maintainer_email='sega01@go-beyond.org',
    url='https://github.com/sporestack/bitcash',
    download_url='https://github.com/sporestack/bitcash/tarball/{}'.format(
        version),
    license='MIT',

    keywords=[
        'bitcoincash',
        'cryptocurrency',
        'payments',
        'tools',
        'wallet',
    ],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],

    install_requires=['coincurve>=4.3.0', 'requests', 'cashaddress==1.0.4'],
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

from setuptools import setup

setup(
    name='site-scanner',
    version='0.2', 
    py_modules=['scanner'],
    install_requires=[
        'ping3>=4.0.0',
        'httpx>=0.24.0',
        'colorama>=0.4.6',
    ],
)
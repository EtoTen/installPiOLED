import glob
import subprocess
from setuptools import setup, find_packages, Extension

setup(
    name='pioled',
    version='1.0',
    description='Adafruit PiOLED for the NVIDIA Jetson Nano',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'luma.oled',
        'luma.core',
    ],
    package_data={},
    platforms=["linux", "linux2"]
)

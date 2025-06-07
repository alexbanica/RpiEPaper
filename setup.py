import sys, os
from setuptools import setup

dependencies = ['Pillow', 'gpiozero', 'docker', 'natsort', 'paramiko', 'PyYAML']

if os.path.exists('/sys/bus/platform/drivers/gpiomem-bcm2835'):
    dependencies += ['RPi.GPIO', 'spidev']
elif os.path.exists('/sys/bus/platform/drivers/gpio-x3'):
    dependencies += ['Hobot.GPIO', 'spidev']
else:
    dependencies += ['Jetson.GPIO']

setup(
    name='cluster-monitor',
    version='1.0.0',
    description='Server Status Display for Raspberry Pi with e-Paper Display',
    long_description='A monitoring system that displays server statistics, Docker swarm information, and system metrics on an e-Paper display',
    author='Alex Banica',
    author_email='ionut.alexandru.banica@gmail.com',
    python_requires='>=3.9',
    package_dir={'': 'cluster_monitor', 'waveshare_epd': 'lib/waveshare_epd'},
    packages=['cluster_monitor', 'waveshare_epd'],
    install_requires=dependencies,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.9',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Monitoring',
    ],
)

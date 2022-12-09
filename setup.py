# -*- coding: utf-8 -*-
#!/usr/bin/env python
#

from setuptools import setup, find_packages

try:
	from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
	class bdist_wheel(_bdist_wheel):
		def finalize_options(self):
			_bdist_wheel.finalize_options(self)
			self.root_is_pure = False
except ImportError:
	bdist_wheel = None

description="Laser Aided Profiler Data Access Library"

setup(
	name="lap_data",
	version="4.0.44",
	description=description,
	long_description=description,
	long_description_content_type="text/markdown",
	author="Peter Demján",
	author_email="peter.demjan@gmail.com",
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Science/Research",
		"Topic :: Database",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Programming Language :: Python :: 3.10",
		"Operating System :: Microsoft :: Windows :: Windows 10",
	],
	keywords="database, graph",
	package_dir={"": "src"},
	packages=find_packages(where="src"),
	python_requires=">=3.10, <4",
	install_requires=[
		'deposit_gui>=1.4.35, <1.5',
	],
	cmdclass={'bdist_wheel': bdist_wheel},
)

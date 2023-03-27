from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in frappe_m365/__init__.py
from frappe_m365 import __version__ as version

setup(
	name="frappe_m365",
	version=version,
	description="Microdoft 365 Groups integration",
	author="aptitudetech",
	author_email="hello@aptitudetech.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)

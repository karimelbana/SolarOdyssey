from setuptools import find_packages
from setuptools import setup

with open("requirements.txt") as f:
    content = f.readlines()
requirements = [x.strip() for x in content if "git+" not in x]

setup(name='solarodyssey',
      version="0.0.1",
      description="SolarOdyssey Model (api_pred)",
      author="Karim Elbana, Arnoud de Haan, Josef Perara, Jonathan Büning",
      url="https://github.com/karimelbana/SolarOdyssey/",
      install_requires=requirements,
      packages=find_packages(),
      # include_package_data: to install data from MANIFEST.in
      include_package_data=True,
      zip_safe=False)

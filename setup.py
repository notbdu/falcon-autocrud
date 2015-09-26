from setuptools import setup

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    long_description = open('README.md').read()

setup(name='falcon-autocrud',
      version='0.0.1',
      description='Makes RESTful CRUD easier',
      long_description=long_description,
      url='https://bitbucket.org/garymonson/falcon-autocrud',
      author='Gary Monson',
      author_email='gary.monson@gmail.com',
      license='MIT',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3',
      ],
      keywords='falcon crud rest database',
      packages=['falcon_autocrud'],
      install_requires=[
          'falcon',
          'falconjsonio',
          'sqlalchemy',
      ],
      zip_safe=False)

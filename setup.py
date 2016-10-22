from setuptools import setup

version = '1.0.23'

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    long_description = open('README.md').read()

setup(name='falcon-autocrud',
      version=version,
      description='Makes RESTful CRUD easier',
      long_description=long_description,
      url='https://bitbucket.org/garymonson/falcon-autocrud',
      author='Gary Monson',
      author_email='gary.monson@gmail.com',
      license='MIT',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Topic :: Database :: Front-Ends',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
      ],
      keywords='falcon crud rest database',
      packages=['falcon_autocrud'],
      install_requires=[
          'falcon >= 1.0.0',
          'falconjsonio >= 0.1.10',
          'sqlalchemy',
      ],
      zip_safe=False)

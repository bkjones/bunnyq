from setuptools import setup, find_packages

version = '1.0.2'

setup(name='bunnyq',
      version=version,
      description="A command shell and CLI app for testing/administering RabbitMQ " \
                  "using its RESTful HTTP Management API.",
      summary="A command shell for testing/administering RabbitMQ " \
                  "using its RESTful HTTP Management API.",
      long_description="A command shell and CLI app for testing/administering RabbitMQ " \
                  "using its RESTful HTTP Management API.",
      docs_url='http://github.com/bkjones/bunnyq',
      classifiers=[
          "Intended Audience :: Developers",
          "Intended Audience :: System Administrators",
          "License :: OSI Approved :: MIT License",
          "Natural Language :: English",
          "Operating System :: POSIX",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Topic :: Internet :: WWW/HTTP",
          ],
      keywords='python http amqp rabbit rabbitmq management',
      install_requires = ['pyyaml', 'pyrabbit', 'argparse'],
      author='Brian K. Jones',
      author_email='bkjones@gmail.com',
      maintainer='Brian K. Jones',
      maintainer_email='bkjones@gmail.com',
      url='http://www.github.com/bkjones/bunnyq',
      download_url='http://www.github.com/bkjones/bunnyq',
      license='MIT',
      packages=find_packages(exclude='tests'),
      include_package_data=False,
      py_modules=['bunnyq'],
      entry_points=dict(console_scripts=['bunnyq=bunnyq:main']),
      zip_safe=False
      )

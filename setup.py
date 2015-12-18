from setuptools import setup
import os

setup(
    name='FlaskSearch',
    version='0.1',
    url='https://github.com/dhamaniasad/Flask-Search',
    license='BSD',
    author='Asad Dhamani',
    author_email='dhamaniasad+code@gmail.com',
    description='Powerful search functionality for Flask apps via ElasticSearch',
    py_modules=['flask_search'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[x.strip() for x in
                      open(os.path.join(os.path.dirname(__file__),
                                        'requirements.txt'))],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

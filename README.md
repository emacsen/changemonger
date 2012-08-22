Changemonger
============


OSM Change monitoring tools
---------------------------

Changemonger is a tool to allow humans to monitor and understand
changes that occur in OpenStreetMap (or API compatible) datasets.

Changemonger provides several services to this end, including a web
frontend and a simple, RESTful API to deliver data to users.


Installation
------------

For most users of this service, installation is unnecessary and they
should use RESTful API calls to make their requests.

For those of you wishing to actually install and run this program 
locally, this program is a standard Python app. It is highly recommended 
that you use `virtualenv` to manage the installation, create a virtual
environment and, from there, just run

    pip install -r requirements.txt

to install the dependencies.

To run the web application, simply run `app.py` with Python, or as a WSGI
application under your web server of choice.


License
-------

This program is covered under the Affero GNU General Public License
version 3 or above as described in the `LICENSE` file enclosed with
the source code

The exception to this are the configuration files under the `features`
directory, including the `magic.py` file, which contains additional
instructions for matching configuration. Modifications beyond simple
configuration shall be covered under the AGPL no matter what
filename/directory they reside in.


OSM Data and Terms of Use
-------------------------

While this program is covered under the AGPLv3, the data it returns
(though modified through Changemonger) is subject to the terms and
licenses of the data source.

In addition, users of this program should be aware that mis-use of
this program could easily run you afoul of OpenStreetMap Terms of
Use. Please refer to them when deploying this application, or better
yet, deploy it only against an API server that you either control or
have a contractual relationship to use.


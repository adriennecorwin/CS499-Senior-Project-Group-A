"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# add the hellodjango project path into the sys.path
sys.path.append('/home/ec2-user/CS499-Senior-Project-A/mysite/')
# add the virtualenv site-packages path to the sys.path
sys.path.append('/home/ec2-user/eb-virt/lib/python3.6/dist-packages')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

application = get_wsgi_application()

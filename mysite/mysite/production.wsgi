import os
os.environ['CONSUMER_KEY']="m5ydxb189UmDg1Ogzl0hKyiy9"
os.environ['CONSUMER_SECRET']="SPNFQvJXE9O5gz7lj1hO4d7xlHieQBldObXwIte2jgKUToups2"
os.environ['ACCESS_TOKEN']="1176877630382985217-tevxv5Voykpl9JJKxJb9dXZMxe07Tu"
os.environ['ACCESS_TOKEN_SECRET']="Ap2yaVjF3a1XA6KHrrGPrfdKetnevfRSFwdURVmshS5g4"
os.environ['DJANGO_SECRET_KEY']="s01#t)uu3#x&$@!96t=#x$#p3tnmqr7_79t*c@vlet5z2n!j(w"
os.environ['DB_HOST']="127.0.0.1"
os.environ['DB_PORT']="3306"
os.environ['DB_USER']="root"
os.environ['DB_PASSWORD']="cs499"
os.environ['ADMIN_EMAILS']=['adriennecorwin@gmail.com', 'michael.zilis@uky.edu', 'justin.wedeking@uky.edu']
os.environ['EMAIL_HOST_USER']="cs499teamA@gmail.com"
os.environ['EMAIL_HOST_PASSWORD']="SCOTUSTwitter2019"

from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
application = get_wsgi_application()

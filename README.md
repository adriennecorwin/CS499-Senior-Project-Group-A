# CS499-Senior-Project-Group-A

currently the website url is http://scotusapp.aws.uky.edu/scotustwitter/

access if only allowed if on uky wifi or if using uky vpn

## Locally

Create a virtual environment for the project to run in (using python 3.6)

    virtualenv -p python3.6 /path/to/yourenv

Download mysql locally

Use this command to access mysql command line

    /usr/local/mysql/bin/mysql -uroot -p

Execute in mysql command line

    mysql > create database SupremeCourtTwitter;

Execute in local repo directory

    pip install Django
  
    pip install django-materialize
  
    pip install mysqlclient
  
    pip install tweepy
  
    pip install textstat
  
    pip install vaderSentiment

Inside the mysite folder of project directory

    python manage.py migrate

    python manage.py makemigrations

    python manage.py migrate

    python manage.py runserver
  
 Navigate to localhost:8000
 
 ## Deploy to Apache server on AWS ec2 instace
 
 ssh into the instance 
 
    ssh -i "{pemfilename}.pem" ec2-user@{ec2ip}
  
 git clone this repository into the home/ec2-user directory
 
 create a python 3.6 virtual environment 
 
 install dependencies (make sure pip is for python 3.6)
 
    pip install -r requirements.txt 
    
 install httpd-devel
 
    sudo yum install httpd24-devel
 
 install mod_wsgi
 
    sudo python3.6 -m pip install mod_wsgi
    
 add load mod_wsgi
 
    vi /etc/httpd/conf.modules.d/mod_wsgi36.conf
    
 write the following to the file
 
    LoadModule wsgi_module "/usr/local/lib64/python3.6/site-packages/mod_wsgi/server/mod_wsgi-py36.cpython-36m-x86_64-linux-gnu.so"
 
 this should be the output of the following command
 
    /usr/local/bin/mod_wsgi-express module-config
 
 create an apache config file for the django app (possibly /etc/httpd/conf.d/django.conf)
 
 write the following to the .conf file
 
     <VirtualHost *:80>
        Alias /static /home/ec2-user/CS499-Senior-Project-Group-A/mysite/myapp/static
        <Directory /home/ec2-user/CS499-Senior-Project-Group-A/mysite/myapp/static>
            Require all granted
        </Directory>

        <Directory /home/ec2-user/CS499-Senior-Project-Group-A/mysite/mysite>
            <Files production.wsgi>
                Require all granted
            </Files>
        </Directory>

        WSGIDaemonProcess mysite python-path=/home/ec2-user/CS499-Senior-Project-Group-A/mysite python-home=/path/to/virtualenv
        WSGIProcessGroup mysite
        WSGIScriptAlias /scotustwitter /home/ec2-user/CS499-Senior-Project-Group-A/mysite/mysite/production.wsgi
    </VirtualHost>
  
 restart the server
 
    sudo apachectl restart
 
 navigate to ec2domain/scotustwitter 
 
 
 ### Known Bugs
 
 1)Logout of admin page redirect to login of website
 
 2)Admin page doesn't seem to render correctly on deployed site

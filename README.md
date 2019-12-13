# CS499-Senior-Project-Group-A

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
 
 install dependencies
 
    pip install -r requirements.txt (make sure pip is for python 3.6)
  
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

        WSGIDaemonProcess mysite python-path=/home/ec2-user/CS499-Senior-Project-Group-A/mysite python-home=/home/ec2-user/eb-virt
        WSGIProcessGroup mysite
        WSGIScriptAlias /scotustwitter /home/ec2-user/CS499-Senior-Project-Group-A/mysite/mysite/production.wsgi
    </VirtualHost>
 
 python-home should be the path to your virtual environment
 
 restart the server
 
    sudo apachectl restart
 
 navigate to ec2domain/scotustwitter 

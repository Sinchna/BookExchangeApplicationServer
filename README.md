# BookExchangeApplicationServer
1.  Clone the repository:
   ```bash
   git clone https://github.com/2023tm93682/book-exchange-platform-server.git
   ```

1. Install [Python](https://www.python.org/) (version 3.8 or higher recommended)
   - Verify installation:
     ```bash
     python --version
     pip --version
     ```

2. Install a virtual environment tool (optional but recommended):
   ```bash
   pip install virtualenv
   ```

3. Install Prerequistes
   ```bash
   pip install djangorestframework djangorestframework-simplejwt
   pip install django-filter
   pip install django-csp
   pip install django-cqrs
   pip install mysqlclient
   pip install sendgrid
   ```
 
4. Install MySQL Server
   Download and install the MySQL Server and MySQL Workbench.
   Create a new database for the project (e.g., book_exchange).
   Note the database credentials (username, password, hostname, and database name).
   
5. Follow the below commands to create the tables and run the application
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver

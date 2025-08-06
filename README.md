# CashG Banking Application

A modern Django-based banking application with secure transaction management.

## Features

- User authentication and account management
- Deposit and withdrawal functionality
- Money transfer between accounts
- Transaction history and reporting
- Modern responsive UI with Tailwind CSS
- Secure banking operations

## Deployment on Render.com

### Prerequisites

1. GitHub repository with your code
2. Render.com account

### Deployment Steps

1. **Connect to GitHub**
   - Go to Render.com dashboard
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure the Web Service**
   - **Name:** `cashg-banking-app` (or your preferred name)
   - **Root Directory:** Leave blank (or set to `CashG` if needed)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn CashG.CashG.wsgi:application`

3. **Environment Variables**
   Add these environment variables in Render:
   - `SECRET_KEY`: Your Django secret key
   - `DATABASE_URL`: (Provided by Render if using their database)

4. **Deploy**
   - Click "Create Web Service"
   - Wait for the build to complete

## Troubleshooting 500 Errors

If you encounter a 500 server error:

1. **Check the test endpoint:** Visit `your-app-url/test/` to see if the server is running
2. **Check Render logs:** Go to your service → "Logs" tab
3. **Common issues:**
   - Missing environment variables
   - Database connection issues
   - Static files not collected
   - Import errors in views or models

## Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd CashG
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
CashG/
├── CashG/                 # Django project settings
│   ├── settings.py       # Main settings file
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI application
├── CashGApp/             # Main Django app
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── urls.py           # App URL patterns
│   └── templates/        # HTML templates
├── requirements.txt      # Python dependencies
├── Procfile             # Deployment configuration
└── build.sh             # Build script
```

## Security Features

- CSRF protection on all forms
- Secure password validation
- Transaction atomicity
- Input validation and sanitization
- Secure session management

## Support

If you encounter any issues:
1. Check the Render logs for error details
2. Ensure all environment variables are set
3. Verify database connectivity
4. Check that all dependencies are installed

## License

This project is for educational purposes.

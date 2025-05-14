# Setting Up Google Authentication for TukkerLa

This guide walks you through setting up Google Authentication for your TukkerLa application.

## 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"

## 2. Configure OAuth Consent Screen

1. Click on "OAuth consent screen" in the sidebar
2. Select "External" user type (or "Internal" if this is only for your organization)
3. Fill in the required information:
   - App name: "TukkerLa"
   - User support email: Your email
   - Developer contact information: Your email
4. Click "Save and Continue"
5. Add the following scopes:
   - `email`
   - `profile`
   - `openid`
6. Click "Save and Continue"
7. Add test users if this is in development
8. Click "Save and Continue"

## 3. Create OAuth 2.0 Client ID

1. Click on "Credentials" in the sidebar
2. Click "Create Credentials" and select "OAuth client ID"
3. Application type: "Web application"
4. Name: "TukkerLa Web Client"
5. Add authorized JavaScript origins:
   - For development: `http://localhost:3000` (or whichever port your frontend runs on)
   - For production: Your domain (e.g., `https://yourapp.com`)
6. Add authorized redirect URIs:
   - For development: `http://localhost:3000/auth/google/callback`
   - For production: `https://yourapp.com/auth/google/callback`
7. Click "Create"

## 4. Copy Client ID and Secret

After creating the credentials, you'll see a popup with your Client ID and Client Secret. Copy these values to your `.env` file:

```
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

## 5. Run Database Migration

Run the migration to add Google authentication fields to the User model:

```bash
cd /path/to/tukkerla
python -m alembic upgrade head
```

## 6. Implement Frontend Authentication

In your frontend application, implement the Google authentication flow:

1. Redirect the user to the Google authentication URL:
   ```
   fetch('http://your-api-url/auth/google/url?redirect_uri=http://your-frontend-url/auth/google/callback')
     .then(response => response.json())
     .then(data => window.location.href = data.auth_url);
   ```

2. Handle the callback to exchange the authorization code for a token:
   ```
   const code = new URLSearchParams(window.location.search).get('code');
   
   fetch('http://your-api-url/auth/google/callback', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       code: code,
       redirect_uri: 'http://your-frontend-url/auth/google/callback'
     })
   })
   .then(response => response.json())
   .then(data => {
     // Store the access token
     localStorage.setItem('token', data.access_token);
     // Redirect to dashboard or home page
     window.location.href = '/dashboard';
   });
   ```

## 7. Testing the Integration

1. Start your backend and frontend applications
2. Navigate to your login page
3. Click the "Login with Google" button
4. You should be redirected to Google's authentication page
5. After authenticating, you'll be redirected back to your application and logged in

## Troubleshooting

- Ensure your redirect URIs match exactly what you've configured in the Google Cloud Console
- Check that the `.env` file contains the correct Client ID and Secret
- Verify that the database migration has run successfully
- Check your API logs for any errors during the authentication process 
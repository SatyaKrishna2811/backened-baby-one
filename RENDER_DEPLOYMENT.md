# Render.com Deployment Guide for Meeting Assistant Backend

## Quick Deploy

1. **Connect to Render**
   - Go to [render.com](https://render.com)
   - Connect your GitHub repository: `https://github.com/riteshroshann/meeting-mind-backened-baby-one`

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Select your repository
   - Use these settings:
     ```
     Name: meeting-assistant-backend
     Environment: Python 3
     Build Command: ./build.sh
     Start Command: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 meeting_assistant.wsgi:application
     ```

3. **Environment Variables**
   Add these in Render dashboard:
   ```
   DJANGO_SECRET_KEY=your-generated-secret-key
   DEBUG=False
   BHASHINI_API_KEY=ujzb4jidEwJo1U-IDxGr2iMkRChAw8qrKcKUQsCA1RSOC2rt6ITU3TihElxkmoHA
   GEMINI_API_KEY=AIzaSyDQq1B4ZAsHIwVvK49Sl99up4H4JA0GxGQ
   FRONTEND_URL=https://your-frontend-domain.vercel.app
   PYTHON_VERSION=3.11.0
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete (5-10 minutes)
   - Your backend will be available at: `https://your-service-name.onrender.com`

## Endpoints

- Health Check: `GET /api/health/`
- Process Audio: `POST /api/process-audio/`

## Features

✅ **Production Ready**
- Gunicorn WSGI server
- Static file serving with WhiteNoise
- CORS configured for frontend
- Comprehensive error handling
- Retry logic for API failures
- Audio processing with librosa fallback

✅ **Security**
- Environment variables for secrets
- HTTPS enforcement in production
- XSS and CSRF protection
- Secure headers configured

✅ **Monitoring**
- Health check endpoint
- Comprehensive logging
- Error tracking and retries

## Troubleshooting

**Build Fails:**
- Check build logs in Render dashboard
- Ensure requirements.txt is valid
- Verify Python version compatibility

**502 Bad Gateway:**
- Check if service is running on correct port ($PORT)
- Verify gunicorn start command
- Check application logs

**API Errors:**
- Verify environment variables are set
- Check API key validity
- Monitor service logs for detailed errors

## Performance

- **Workers:** 2 (adjust based on usage)
- **Timeout:** 120s (for audio processing)
- **Memory:** 512MB (upgrade if needed)
- **Auto-scaling:** Available on paid plans

## Cost

- **Free Tier:** 750 hours/month (enough for development)
- **Paid Plans:** Start at $7/month for production workloads

## Support

- Documentation: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

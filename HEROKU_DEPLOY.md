# Heroku Deployment Guide

## Prerequisites
- Heroku CLI installed ([Download here](https://devcenter.heroku.com/articles/heroku-cli))
- Git repository initialized

## Deployment Steps

### 1. Login to Heroku
```bash
heroku login
```

### 2. Create Heroku App
```bash
heroku create your-padel-monitor-app-name
```

### 3. Set Environment Variables
Replace with your actual values:
```bash
heroku config:set TELEGRAM_BOT_TOKEN="7586648733:AAEsyD-NcKxK1kZu_z-k1xPCs6meg7lZ14o"
heroku config:set TELEGRAM_CHAT_ID="-4824881171"
```

### 4. Deploy Code
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### 5. Scale the Worker
Since this is a background monitoring service (not a web app):
```bash
heroku ps:scale worker=1
```

### 6. View Logs
```bash
heroku logs --tail
```

## Important Notes

- **No web dyno needed**: This runs as a worker process
- **24/7 monitoring**: The worker will run continuously 
- **Cost**: Free tier allows 550-1000 dyno hours/month
- **Environment variables**: Credentials are stored securely in Heroku

## Useful Commands

```bash
# Check app status
heroku ps

# Stop monitoring
heroku ps:scale worker=0

# Start monitoring
heroku ps:scale worker=1

# View recent logs
heroku logs --tail

# Open Heroku dashboard
heroku open
```

## Troubleshooting

If deployment fails:
1. Check `heroku logs --tail` for errors
2. Ensure all files are committed to git
3. Verify Procfile exists and is correct
4. Check that requirements.txt includes all dependencies 
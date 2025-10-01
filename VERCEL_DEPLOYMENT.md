# Vercel Deployment Guide for School Upgrade System

## Prerequisites
1. A Vercel account (sign up at https://vercel.com)
2. Git repository with your code
3. Vercel CLI (optional, but recommended)

## Deployment Steps

### Method 1: Using Vercel Dashboard (Recommended)

1. **Prepare your repository:**
   - Make sure your code is in a Git repository (GitHub, GitLab, or Bitbucket)
   - Push all your changes to the main branch

2. **Import to Vercel:**
   - Go to https://vercel.com/dashboard
   - Click "New Project"
   - Import your Git repository
   - Vercel will automatically detect it's a Python project

3. **Configure Build Settings:**
   - Framework Preset: "Other"
   - Root Directory: "./" (leave default)
   - Build Command: (leave empty, it will use requirements.txt)
   - Output Directory: (leave empty)
   - Install Command: `pip install -r requirements.txt`

4. **Deploy:**
   - Click "Deploy"
   - Vercel will build and deploy your application
   - You'll get a URL like: https://your-app-name.vercel.app

### Method 2: Using Vercel CLI

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy from your project directory:**
   ```bash
   cd /Users/macbookpro/Desktop/PMC/SchoolUpgradeSystem
   vercel
   ```

4. **Follow the prompts:**
   - Set up and deploy? Yes
   - Which scope? (select your account)
   - Link to existing project? No
   - Project name? (accept default or enter new name)
   - Directory? (accept default)

## Files Modified for Vercel Deployment

1. **vercel.json** - Vercel configuration
2. **vercel_app.py** - Entry point for Vercel
3. **requirements.txt** - Updated with all dependencies
4. **.vercelignore** - Files to exclude from deployment

## Important Notes

1. **File Storage:** Vercel uses a read-only file system except for `/tmp`. The app has been configured to use `/tmp/uploads` and `/tmp/downloads` on Vercel.

2. **Sample Data:** The balochistan_census.csv file will be included in the deployment for the sample data functionality.

3. **Environment Variables:** If you need to set any environment variables, you can do so in the Vercel dashboard under Project Settings → Environment Variables.

4. **Domain:** After deployment, you can add a custom domain in the Vercel dashboard.

## Troubleshooting

1. **Build Fails:** Check the build logs in the Vercel dashboard for specific error messages.

2. **Import Errors:** Make sure all dependencies are listed in requirements.txt.

3. **File Upload Issues:** Remember that uploaded files are stored in `/tmp` on Vercel and will be cleared between deployments.

4. **Timeout Issues:** Large file processing might hit Vercel's function timeout limit. Consider breaking down large operations.

## Post-Deployment Testing

1. Visit your Vercel URL
2. Test file upload functionality
3. Try the sample data loading
4. Test the school upgrade analysis features

## Updating Your App

To update your deployed app:
1. Push changes to your Git repository
2. Vercel will automatically redeploy (if auto-deployment is enabled)
3. Or manually trigger a deployment from the Vercel dashboard

Your app should now be ready for deployment on Vercel!

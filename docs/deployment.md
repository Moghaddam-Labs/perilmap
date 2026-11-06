# Deploying PerilMap

The API runs on Google Cloud Run in London (`europe-west2`). The built flood and heat files are
bundled into the image, so there's no database or storage bucket to manage.

## Safeguards

| Safeguard | Setting |
|---|---|
| Spend cap on Cloud Run | £1 a month, which pauses Cloud Run without deleting anything |
| Budget alert across the project | £1 a month, for small costs such as image storage |
| Servers | One at most, none when idle |
| Rate limits | 30 requests a minute per visitor, 300 in total |

A spend cap isn't instant, and any overage is still billed. If the cap is reached, the API stops
answering until the next month or until the cap is lifted under **Billing > Budgets and caps**.

## First deployment

Install the [gcloud CLI](https://docs.cloud.google.com/sdk/docs/install), then sign in:

```bash
gcloud auth login
gcloud config set project perilmap
```

Turn on the services and give the build account its role:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
PROJECT_NUMBER="$(gcloud projects describe perilmap --format='value(projectNumber)')"
gcloud projects add-iam-policy-binding perilmap \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role=roles/run.builder --condition=None
```

The role can take a couple of minutes to apply.

## Deploy and check

Put the built data files in `grids/`, then run:

```bash
scripts/deploy.sh
scripts/verify_deployment.sh https://your-service-url
```

Once the website exists, pass its address so browsers can call the API:

```bash
scripts/deploy.sh https://your-website.example
```

## Keep visitors' addresses out of logs

Cloud Run writes its own log of each request, including the visitor's internet address, even though
the app doesn't log them. Exclude those logs:

```bash
gcloud logging sinks update _Default \
  --add-exclusion=name=perilmap-request-logs,filter='LOG_ID("run.googleapis.com/requests")'
```

The app's own error messages and Cloud Run's traffic charts still work.

## Keep image storage small

The free allowance for stored images is 0.5 GB, and each deployment adds an image. Keep only the two
newest:

```bash
gcloud artifacts repositories set-cleanup-policies cloud-run-source-deploy \
  --location=europe-west2 --policy=scripts/image-cleanup-policy.json
```

## Updating the data

Rebuild the files with the data test, replace them in `grids/`, and deploy again.

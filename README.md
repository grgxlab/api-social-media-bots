# API Social Media Bots

This repository contains a collection of social media automation bots built around public APIs
(e.g. Bluesky). The goal is to demonstrate clean API integrations, scheduled posting, and
cross-promotion features between multiple themed accounts (e.g. nature, cats, space, etc.).

## Features
- Scheduled posting via cronjobs
- Unified configuration for multiple bots
- API-based like/engagement automation
- Environment-based secrets (no keys in code)

## Tech Stack
- Language: Python / Node.js (adapt this)
- Scheduler: cron/systemd/… (adapt)
- APIs: Bluesky (and others if applicable)

## Setup
```bash
git clone https://github.com/<your-username>/api-social-media-bots.git
cd api-social-media-bots

# create and fill .env file
# install dependencies
# run your bots

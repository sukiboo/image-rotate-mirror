---
title: Image Rotate Mirror
emoji: 🐱🪞🐱
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.56.0
app_file: app.py
pinned: false
license: mit
short_description: Just a silly little app to make silly little cat pictures
---

| Input | Left mirror | Right mirror |
|---|---|---|
| <img src="images/noodle.jpeg" width="240"> | <img src="images/noodle_left.png" width="240"> | <img src="images/noodle_right.png" width="240"> |

### Usage

1. Upload an image
2. Adjust selection area
3. Download two images

The app is deployed on HF free-tier toaster so it's painfully slow; you can run it locally with:
```
pip install -r requirements.txt
streamlit run app.py
```

### Why

1. I was bored
2. I had tokens
3. Look at that cat

### License

Always MIT

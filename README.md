# 🚀 Crystal Framework Config Generator

A complete Flask web application to **create Executor Config JSONs** and **Metadata Insert SQLs** for onboarding events into the Crystal Framework.

---

# 📚 Table of Contents

- [About the Project](#about-the-project)
- [Full Features](#full-features)
- [Project Structure](#project-structure)
- [How it Works (End-to-End Flow)](#how-it-works-end-to-end-flow)
- [Screens and Pages](#screens-and-pages)
- [Installation & Running Locally](#installation--running-locally)
- [Examples](#examples)
- [Future Enhancements](#future-enhancements)
- [Credits](#credits)

---

# 📖 About the Project

Crystal Config Generator simplifies the manual task of creating event onboarding JSONs into a **visual flow** where users:

- Fill structured forms
- Preview JSON live
- Save each stage
- Download a final ready-to-use config file.

---

# ✨ Full Features

- 🖊 **Create Executor Configs** (Truncate ➔ Stage Load ➔ Base Load)
- 🧩 **Session Based Saving** (each block stored safely)
- 📝 **Live JSON Preview** while filling forms
- 🎯 **Validation** to prevent missing data
- 📥 **Download final JSON** directly
- 📋 **Create Metadata SQL (Coming Soon)**
- 🎨 **Modern UI with SweetAlert popups**

---

# 🏗 Project Structure

flask_project/ │ ├── app.py # Flask backend: all routes, logic, session │ ├── templates/ # Front-end HTML templates │ ├── index.html # Landing page (event name input) │ ├── add_truncate.html # Truncate stage form + preview │ ├── add_stage_load.html# Stage Load form + preview │ ├── add_base_load.html # Base Load form + preview │ ├── preview.html # Full event config preview and download │ └── start_metadata.html# Coming soon │ ├── static/ # (Optional) static CSS/JS if needed │ └── README.md # Documentation (this file)
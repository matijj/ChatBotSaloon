# Dialogflow Chatbot for Scheduling & Rescheduling  


This is a **Dialogflow chatbot** designed to handle **scheduling and rescheduling appointments** using natural language. It connects to **Google Calendar** for real-time availability, includes **input validation**, and has **fallback recovery** with **LLM-powered responses for FAQs**.  



## 🔹 Features  

✅ **Schedule & Reschedule Appointments** – Finds available 30-minute slots and suggests alternatives if needed.  
✅ **Google Calendar Integration** – Checks availability and books appointments in real-time.  
✅ **Fallback Recovery** – Reminds users to provide missing info (like name) and handles misunderstandings.  
✅ **LLM-Powered FAQ Responses** – If no active context is found, the chatbot answers general business-related questions using an LLM.  
✅ **Validation** – Ensures correct name, email, and date-time format before proceeding.  
✅ **Webhook-Based Processing** – Uses a structured backend to handle requests.  
✅ **Rich UI Elements** – Supports buttons and quick replies.  
✅ **Deployed on Heroku** – Runs live on a cloud platform.  



## 📌 Installation & Setup  

### 1️⃣ Running Locally  

### **Requirements**  
- Python 3.10+  
- A Google Cloud Project with access to Google Calendar API  
- A Dialogflow ES Agent  
- A **Service Account JSON Key** for Google authentication  
- **ngrok** (to expose the local server to Dialogflow)  

### **Clone the Repository**  
```bash
git clone <your-repo-url>
cd <your-project-folder>
```

### **Create a Virtual Environment & Install Dependencies**
```bash
python -m venv venv
pip install -r requirements.txt
```


### **Set Up Environment Variables**
```bash
OPENAI_API_KEY=
PORT=5000
CREDENTIALS=
CALENDAR_ID=
```


### **Run the Flask Server**
```bash
python run.py
```
The bot should now be running on http://localhost:5000/.


### **Expose the Local Server to Dialogflow Using ngrok**
```bash
ngrok http 5000
```
This will generate a temporary public URL like
```bash
https://988d-79-101-72-162.ngrok-free.app
```


### **Connect Webhook to Dialogflow**

#### In the Dialogflow Console:
#### 1.Go to Fulfillment > Webhook
#### 2.Set the webhook URL to:

```bash
https://YOUR_NGROK_URL/webhook
```

Example:

```bash
https://988d-79-101-72-162.ngrok-free.app/webhook

```

3. Save changes and test the bot.




### **Deployment**

This bot is deployed on Heroku, but it can run on any platform that supports Flask.
If you want to deploy it on Heroku, follow their official guide:
Heroku Deployment Docs

🔗 Live Demo: https://bot-salona-f40de31fc167.herokuapp.com/







### **📂 Code Structure**
```bash
📦 your-project-folder
│-- 📂 src
│   ├── app.py               # Main Flask app handling requests
│
│-- 📂 static                 # Stores static assets (e.g., images)
│   ├── double-hitter.jpg
│   ├── shampoo-one.jpg
│   ├── tea-tree-shampoo.jpg
│
│-- 📂 templates              # Contains chatbot UI
│   ├── index.html
│
│-- 📂 tests                  # Contains test cases (not detailed here)
│
│-- 📂 utils                   # Contains helper modules
│   ├── action_handlers.py    # Handles different user actions
│   ├── calendar_services.py  # Manages Google Calendar API calls
│   ├── config.py             # Configuration settings
│   ├── helper_functions.py   # Utility functions for validation, logging, etc.
│
│-- .python-version           # Python version file
│-- Procfile                  # Heroku process file
│-- README.md                 # Documentation
│-- requirements.txt          # Dependencies
│-- run.py                    # Starts the Flask app

```


### **🛠 Future Improvements**

** Works best with round numbers for now **

** Timezone Adjustments** – Currently, the bot assumes a fixed timezone. Implement dynamic timezone handling for users worldwide.

** Improve Email Validation Handling ** – Right now, if a user forgets special characters like @, the bot just throws an error instead of explaining what’s wrong. Fix the validation logic to provide clear feedback to the user.

** Fix "10h" Time Parsing Bug ** – When users enter times like "10h" or "6h", the bot always defaults to 12:00 H instead of the correct hour. Other formats (like "10 AM" or "tomorrow 10") work fine. Investigate and fix the parsing issue.

 

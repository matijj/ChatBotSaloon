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
venv\Scripts\activate
pip install -r requirements.txt
```


### **Set Up Environment Variables**
```bash
PORT=5000
OPENAI_API_KEY=
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

In the Dialogflow Console:
1.Go to Fulfillment > Webhook
Set the webhook URL to:

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

🔗 Live Demo: [YOUR_HEROKU_LINK]







### **📂 Code Structure**
lua
Copy
📦 your-project-folder
│-- 📂 src
│   │-- app.py              # Main Flask app handling requests
│   │-- action_handlers.py   # Handles different user actions
│   │-- calendar_services.py # Manages Google Calendar API calls
│   │-- helper_functions.py  # Utility functions for validation, logging, etc.
│-- 📂 templates
│   │-- index.html           # Chatbot UI
│-- run.py                   # Starts the Flask app
│-- config.py                 # Configuration settings
│-- requirements.txt          # Dependencies
│-- README.md                 # This file


### **🛠 Future Improvements**
**✅ Dynamic Fallback Recovery** – Make the chatbot answer open-ended fallback questions instead of just predefined responses.

**✅ Timezone Adjustments** – Currently, the bot assumes a fixed timezone. Implement dynamic timezone handling for users worldwide.

**✅ LLM Integration for Responses** – Instead of predefined messages, use GPT for more natural responses.


 

from flask import Flask, render_template, jsonify, request, session
from flask_pymongo import PyMongo
from bson import json_util
import json
import os
from datetime import datetime
from bson.objectid import ObjectId
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB Configuration
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/portfolio")
mongo = PyMongo(app)

# OpenRouter API Key
OPENROUTER_API_KEY = "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"

# Collections
resume_collection = mongo.db.resume
messages_collection = mongo.db.messages
visitors_collection = mongo.db.visitors
chat_history_collection = mongo.db.chat_history

@app.route('/')
def index():
    # Track visitor
    visitor_data = {
        "ip": request.remote_addr,
        "user_agent": str(request.user_agent),
        "timestamp": datetime.now()
    }
    visitors_collection.insert_one(visitor_data)
    
    # Get resume data from MongoDB
    resume_data = resume_collection.find_one({"email": "arajasuhrita@gmail.com"})
    
    if not resume_data:
        # Insert default resume data if not exists
        default_resume = {
            "name": "ARAJA SUHRITA",
            "email": "arajasuhrita@gmail.com",
            "phone": "9398545812",
            "profile_summary": "Motivated and dedicated B.Tech student with a strong academic record (CGPA: 9.13). Possessing foundational knowledge in C programming and strong communication skills. Eager to learn new technologies and contribute effectively to organizational growth.",
            "about": "I am a passionate B.Tech student with a keen interest in software development and emerging technologies. With a strong foundation in programming and excellent communication skills, I strive to create innovative solutions that make a difference.",
            "achievements": [
                "Academic Excellence Award - 2023",
                "Best Project Award in College Tech Fest",
                "Certificate of Merit in Coding Competition",
                "Volunteer Coordinator at College Events"
            ],
            "services": [
                {
                    "icon": "code",
                    "title": "Web Development",
                    "description": "Building responsive and modern websites using latest technologies"
                },
                {
                    "icon": "mobile-alt",
                    "title": "C Programming",
                    "description": "Efficient C programming solutions for various applications"
                },
                {
                    "icon": "paint-brush",
                    "title": "UI/UX Design",
                    "description": "Creating beautiful and intuitive user interfaces"
                },
                {
                    "icon": "chart-line",
                    "title": "Technical Support",
                    "description": "Providing technical assistance and troubleshooting"
                }
            ],
            "education": [
                {"degree": "B.Tech", "institution": "Current University", "cgpa": "9.13", "year": "2022-2026"},
                {"degree": "Intermediate", "institution": "Star Junior College", "cgpa": "9.7", "year": "2020-2022"},
                {"degree": "10th Class", "institution": "Dr. K.K.R's Gowtham School", "cgpa": "9.3", "year": "2020"}
            ],
            "projects": [
                {
                    "title": "Portfolio Website",
                    "description": "Modern portfolio website with AI chatbot integration",
                    "technologies": ["Flask", "MongoDB", "JavaScript"],
                    "image": "fa-solid fa-laptop-code"
                },
                {
                    "title": "Student Management System",
                    "description": "A comprehensive system to manage student records",
                    "technologies": ["Python", "SQLite"],
                    "image": "fa-solid fa-graduation-cap"
                }
            ],
            "technical_skills": ["C", "Python", "HTML/CSS", "JavaScript", "Flask", "MongoDB"],
            "soft_skills": ["Communication", "Quick Learner", "Teamwork", "Problem Solving", "Leadership"],
            "hobbies": ["Dance", "Music", "Chess", "Reading", "Travel"],
            "languages": ["Telugu (Native)", "English (Fluent)"],
            "social_links": {
                "github": "#",
                "linkedin": "#",
                "twitter": "#"
            }
        }
        resume_collection.insert_one(default_resume)
        resume_data = default_resume
    
    return render_template('index.html', resume=resume_data)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = session.get('session_id', str(datetime.now().timestamp()))
        session['session_id'] = session_id
        
        # Get resume context for the AI
        resume_data = resume_collection.find_one({"email": "arajasuhrita@gmail.com"})
        
        # Create context for AI
        context = f"""
        You are a helpful assistant for ARAJA SUHRITA's portfolio website. Here's information about Araja Suhrita:
        
        Name: {resume_data.get('name', 'ARAJA SUHRITA')}
        Email: {resume_data.get('email', 'arajasuhrita@gmail.com')}
        Phone: {resume_data.get('phone', '9398545812')}
        About: {resume_data.get('about', 'B.Tech student')}
        Education: {', '.join([f"{e.get('degree', '')} ({e.get('cgpa', '')} CGPA)" for e in resume_data.get('education', [])])}
        Technical Skills: {', '.join(resume_data.get('technical_skills', []))}
        Soft Skills: {', '.join(resume_data.get('soft_skills', []))}
        Services: {', '.join([s.get('title', '') for s in resume_data.get('services', [])])}
        
        Please answer questions about Araja Suhrita professionally and helpfully. Keep responses concise and friendly.
        """
        
        # Call OpenRouter API
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_message}
                ]
            }
        )
        
        ai_response = response.json()
        bot_message = ai_response['choices'][0]['message']['content']
        
        # Save chat history
        chat_data = {
            "session_id": session_id,
            "user_message": user_message,
            "bot_message": bot_message,
            "timestamp": datetime.now()
        }
        chat_history_collection.insert_one(chat_data)
        
        return jsonify({
            "success": True,
            "message": bot_message,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "I'm having trouble responding right now. Please try again later."
        }), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    try:
        session_id = session.get('session_id')
        if session_id:
            history = list(chat_history_collection.find(
                {"session_id": session_id}
            ).sort("timestamp", -1).limit(50))
            return jsonify(json.loads(json_util.dumps(history)))
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def contact():
    try:
        data = request.json
        
        # Validate required fields
        if not all(k in data for k in ('name', 'email', 'message')):
            return jsonify({
                "success": False, 
                "message": "All fields are required"
            }), 400
        
        # Create message document
        message_data = {
            "name": data.get('name'),
            "email": data.get('email'),
            "message": data.get('message'),
            "timestamp": datetime.now(),
            "read": False,
            "ip_address": request.remote_addr,
            "user_agent": str(request.user_agent)
        }
        
        # Insert into MongoDB
        result = messages_collection.insert_one(message_data)
        
        return jsonify({
            "success": True, 
            "message": "Message sent successfully! I'll get back to you soon.",
            "message_id": str(result.inserted_id)
        })
        
    except Exception as e:
        print(f"Error saving message: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "Failed to send message. Please try again."
        }), 500

@app.route('/api/visitor-count', methods=['GET'])
def visitor_count():
    try:
        count = visitors_collection.count_documents({})
        return jsonify({"count": count})
    except Exception as e:
        return jsonify({"count": 0, "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
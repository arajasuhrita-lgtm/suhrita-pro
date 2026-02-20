from flask import Flask, render_template, jsonify, request
from flask_pymongo import PyMongo
from bson import json_util
import json
import os
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB Configuration
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/portfolio")
mongo = PyMongo(app)

# Collections
resume_collection = mongo.db.resume
messages_collection = mongo.db.messages
visitors_collection = mongo.db.visitors

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

@app.route('/api/resume', methods=['GET'])
def get_resume():
    resume = resume_collection.find_one({"email": "arajasuhrita@gmail.com"})
    return jsonify(json.loads(json_util.dumps(resume)))

@app.route('/api/update-resume', methods=['POST'])
def update_resume():
    data = request.json
    result = resume_collection.update_one(
        {"email": "arajasuhrita@gmail.com"},
        {"$set": data},
        upsert=True
    )
    return jsonify({"success": True, "modified": result.modified_count})

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

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Admin endpoint to view all messages"""
    try:
        messages = list(messages_collection.find().sort("timestamp", -1))
        return jsonify(json.loads(json_util.dumps(messages)))
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/messages/<message_id>/read', methods=['PUT'])
def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        result = messages_collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"read": True}}
        )
        return jsonify({"success": True, "modified": result.modified_count})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/messages/<message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a message"""
    try:
        result = messages_collection.delete_one({"_id": ObjectId(message_id)})
        return jsonify({"success": True, "deleted": result.deleted_count})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/visitor-count', methods=['GET'])
def visitor_count():
    try:
        count = visitors_collection.count_documents({})
        return jsonify({"count": count})
    except Exception as e:
        return jsonify({"count": 0, "error": str(e)})

@app.route('/admin/messages')
def admin_messages():
    """Simple admin page to view messages"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Message Admin</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #333; }
            .message { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .unread { border-left: 4px solid #667eea; }
            .read { opacity: 0.7; }
            .timestamp { color: #666; font-size: 0.9em; }
            .actions { margin-top: 10px; }
            button { padding: 5px 15px; margin-right: 10px; cursor: pointer; border: none; border-radius: 4px; }
            .mark-read { background: #28a745; color: white; }
            .delete { background: #dc3545; color: white; }
            .refresh { background: #667eea; color: white; padding: 10px 20px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Contact Messages</h1>
            <button class="refresh" onclick="loadMessages()">Refresh Messages</button>
            <div id="messages"></div>
        </div>
        
        <script>
            async function loadMessages() {
                try {
                    const response = await fetch('/api/messages');
                    const messages = await response.json();
                    displayMessages(messages);
                } catch (error) {
                    console.error('Error loading messages:', error);
                }
            }
            
            function displayMessages(messages) {
                const container = document.getElementById('messages');
                if (messages.length === 0) {
                    container.innerHTML = '<p>No messages yet.</p>';
                    return;
                }
                
                container.innerHTML = messages.map(msg => `
                    <div class="message ${msg.read ? 'read' : 'unread'}">
                        <h3>${msg.name}</h3>
                        <p><strong>Email:</strong> ${msg.email}</p>
                        <p><strong>Message:</strong> ${msg.message}</p>
                        <p class="timestamp">${new Date(msg.timestamp.$date).toLocaleString()}</p>
                        <p><small>IP: ${msg.ip_address || 'N/A'}</small></p>
                        <div class="actions">
                            ${!msg.read ? `<button class="mark-read" onclick="markRead('${msg._id.$oid}')">Mark as Read</button>` : ''}
                            <button class="delete" onclick="deleteMessage('${msg._id.$oid}')">Delete</button>
                        </div>
                    </div>
                `).join('');
            }
            
            async function markRead(id) {
                try {
                    await fetch(`/api/messages/${id}/read`, { method: 'PUT' });
                    loadMessages();
                } catch (error) {
                    console.error('Error marking message as read:', error);
                }
            }
            
            async function deleteMessage(id) {
                if (confirm('Are you sure you want to delete this message?')) {
                    try {
                        await fetch(`/api/messages/${id}`, { method: 'DELETE' });
                        loadMessages();
                    } catch (error) {
                        console.error('Error deleting message:', error);
                    }
                }
            }
            
            // Load messages on page load
            loadMessages();
        </script>
    </body>
    </html>
    '''

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)

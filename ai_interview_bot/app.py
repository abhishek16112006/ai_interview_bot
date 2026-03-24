from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
import json

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview_practice.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship('Answer', backref='user', lazy=True, cascade='all, delete-orphan')
    resumes = db.relationship('Resume', backref='user', lazy=True, cascade='all, delete-orphan')

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    questions = db.relationship('Question', backref='company', lazy=True, cascade='all, delete-orphan')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), default='technical')
    difficulty = db.Column(db.String(20), default='medium')
    sample_answer = db.Column(db.Text)
    answers = db.relationship('Answer', backref='question', lazy=True)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float)
    feedback = db.Column(db.Text)
    sentiment = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50))
    location = db.Column(db.String(200))
    summary = db.Column(db.Text)
    education = db.Column(db.Text)
    experience = db.Column(db.Text)
    skills = db.Column(db.Text)
    certifications = db.Column(db.Text)
    projects = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({'success': True, 'message': 'Account created successfully'})
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True, 'message': 'Login successful'})
        
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    companies = Company.query.all()
    user = User.query.get(session['user_id'])
    total_answers = Answer.query.filter_by(user_id=session['user_id']).count()
    avg_score = db.session.query(db.func.avg(Answer.score)).filter_by(user_id=session['user_id']).scalar() or 0
    
    return render_template('dashboard.html', 
                         companies=companies, 
                         user=user,
                         total_answers=total_answers,
                         avg_score=round(avg_score, 2))

@app.route('/interview/<int:company_id>')
def interview(company_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company = Company.query.get_or_404(company_id)
    questions = Question.query.filter_by(company_id=company_id).all()
    
    return render_template('interview.html', company=company, questions=questions)

@app.route('/get_question/<int:question_id>')
def get_question(question_id):
    question = Question.query.get_or_404(question_id)
    return jsonify({
        'id': question.id,
        'text': question.question_text,
        'type': question.question_type,
        'difficulty': question.difficulty
    })

@app.route('/analyze_answer', methods=['POST'])
def analyze_answer():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400
    
    question_id = data.get('question_id')
    answer_text = data.get('answer_text')
    
    if not question_id:
        return jsonify({'success': False, 'message': 'Question ID is required'}), 400
    
    if not answer_text or len(answer_text.strip()) < 10:
        return jsonify({
            'success': False, 
            'message': 'Please provide a more detailed answer (at least 10 characters)'
        }), 400
    
    question = Question.query.get_or_404(question_id)
    
    score = calculate_basic_score(answer_text)
    feedback = generate_basic_feedback(answer_text, score)
    sentiment = "neutral"
    analysis = {'strengths': [], 'improvements': []}
    
    if client:
        try:
            ai_analysis = analyze_with_ai(question.question_text, answer_text, question.sample_answer)
            score = ai_analysis.get('score', score)
            feedback = ai_analysis.get('feedback', feedback)
            sentiment = ai_analysis.get('sentiment', sentiment)
            analysis = {
                'strengths': ai_analysis.get('strengths', []),
                'improvements': ai_analysis.get('improvements', [])
            }
        except Exception as e:
            pass
    
    answer = Answer(
        user_id=session['user_id'],
        question_id=question_id,
        answer_text=answer_text,
        score=score,
        feedback=feedback,
        sentiment=sentiment
    )
    db.session.add(answer)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'score': score,
        'feedback': feedback,
        'sentiment': sentiment,
        'strengths': analysis.get('strengths', []),
        'improvements': analysis.get('improvements', [])
    })

def analyze_with_ai(question_text, answer_text, sample_answer=None):
    prompt = f"""You are an expert interview coach. Analyze this interview answer and provide detailed feedback.

Question: {question_text}

Candidate's Answer: {answer_text}

{f"Sample Answer for Reference: {sample_answer}" if sample_answer else ""}

Provide a JSON response with:
1. score (0-100): Overall quality score
2. sentiment (positive/neutral/negative): Tone and confidence level
3. feedback: 2-3 sentence overall assessment
4. strengths: List of 2-3 strong points
5. improvements: List of 2-3 areas to improve

Focus on: clarity, relevance, technical accuracy, confidence, and completeness."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500
    )
    
    result = json.loads(response.choices[0].message.content)
    return result

def calculate_basic_score(answer_text):
    length = len(answer_text)
    if length < 50:
        return 40
    elif length < 100:
        return 60
    elif length < 200:
        return 75
    else:
        return 85

def generate_basic_feedback(answer_text, score):
    if score < 50:
        return "Your answer is too brief. Try to provide more details and examples."
    elif score < 70:
        return "Good start! Consider adding more specific examples and technical details."
    elif score < 85:
        return "Well done! Your answer covers the main points. Add more depth for excellence."
    else:
        return "Excellent answer! Comprehensive and well-structured."

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    answers = Answer.query.filter_by(user_id=session['user_id']).order_by(Answer.created_at.desc()).all()
    return render_template('history.html', answers=answers)

@app.route('/resume', methods=['GET', 'POST'])
def resume():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400
        
        if not data.get('full_name') or not data.get('email'):
            return jsonify({'success': False, 'message': 'Full name and email are required'}), 400
        
        resume = Resume(
            user_id=session['user_id'],
            full_name=data.get('full_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            location=data.get('location'),
            summary=data.get('summary'),
            education=data.get('education'),
            experience=data.get('experience'),
            skills=data.get('skills'),
            certifications=data.get('certifications'),
            projects=data.get('projects')
        )
        db.session.add(resume)
        db.session.commit()
        
        return jsonify({'success': True, 'resume_id': resume.id})
    
    user_resume = Resume.query.filter_by(user_id=session['user_id']).first()
    return render_template('resume.html', resume=user_resume)

@app.route('/download_resume/<int:resume_id>')
def download_resume(resume_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    resume = Resume.query.get_or_404(resume_id)
    
    if resume.user_id != session['user_id']:
        return "Unauthorized", 403
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=6,
        spaceBefore=12,
        borderWidth=1,
        borderColor=colors.HexColor('#3498db'),
        borderPadding=5,
        backColor=colors.HexColor('#ecf0f1')
    )
    
    normal_style = styles['BodyText']
    
    story.append(Paragraph(resume.full_name, title_style))
    
    contact_info = f"{resume.email} | {resume.phone or ''} | {resume.location or ''}"
    story.append(Paragraph(contact_info, normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    if resume.summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
        story.append(Paragraph(resume.summary, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    if resume.experience:
        story.append(Paragraph("EXPERIENCE", heading_style))
        story.append(Paragraph(resume.experience.replace('\n', '<br/>'), normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    if resume.education:
        story.append(Paragraph("EDUCATION", heading_style))
        story.append(Paragraph(resume.education.replace('\n', '<br/>'), normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    if resume.skills:
        story.append(Paragraph("SKILLS", heading_style))
        story.append(Paragraph(resume.skills.replace('\n', '<br/>'), normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    if resume.projects:
        story.append(Paragraph("PROJECTS", heading_style))
        story.append(Paragraph(resume.projects.replace('\n', '<br/>'), normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    if resume.certifications:
        story.append(Paragraph("CERTIFICATIONS", heading_style))
        story.append(Paragraph(resume.certifications.replace('\n', '<br/>'), normal_style))
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{resume.full_name.replace(' ', '_')}_Resume.pdf",
        mimetype='application/pdf'
    )

@app.route('/introduction')
def introduction():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('introduction.html')

@app.route('/analyze_introduction', methods=['POST'])
def analyze_introduction():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400
    
    intro_text = data.get('intro_text')
    
    if not intro_text or len(intro_text.strip()) < 20:
        return jsonify({
            'success': False,
            'message': 'Please provide a more detailed introduction (at least 20 characters)'
        }), 400
    
    score = len(intro_text) // 3
    if score > 100:
        score = 100
    
    feedback = 'Your introduction has been recorded. Configure OpenAI API for detailed AI-powered feedback.'
    strengths = ['Good length', 'Clear communication']
    improvements = ['Add more specific examples', 'Mention key achievements']
    professional_example = intro_text
    
    if client:
        try:
            prompt = f"""You are an expert career coach. Analyze this professional introduction and provide feedback.

Introduction: {intro_text}

Provide a JSON response with:
1. score (0-100): Overall quality score
2. feedback: 2-3 sentence overall assessment
3. strengths: List of 2-3 strong points
4. improvements: List of 2-3 specific suggestions to improve
5. professional_example: A refined version of their introduction

Focus on: clarity, confidence, relevance, professional tone, and structure."""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=600
            )
            
            result = json.loads(response.choices[0].message.content)
            
            score = result.get('score', score)
            feedback = result.get('feedback', feedback)
            strengths = result.get('strengths', strengths)
            improvements = result.get('improvements', improvements)
            professional_example = result.get('professional_example', professional_example)
        except Exception as e:
            pass
    
    return jsonify({
        'success': True,
        'score': score,
        'feedback': feedback,
        'strengths': strengths,
        'improvements': improvements,
        'professional_example': professional_example
    })

def init_db():
    with app.app_context():
        db.create_all()
        
        if Company.query.count() == 0:
            companies = [
                Company(name='Deloitte'),
                Company(name='Cognizant'),
                Company(name='TCS'),
                Company(name='Wipro'),
                Company(name='Microsoft'),
                Company(name='Google')
            ]
            db.session.add_all(companies)
            db.session.commit()
            
            questions_data = [
                ('Deloitte', 'Tell me about yourself and your experience in consulting.', 'behavioral', 'easy'),
                ('Deloitte', 'How do you handle tight deadlines and multiple projects?', 'behavioral', 'medium'),
                ('Deloitte', 'Describe a time when you solved a complex business problem.', 'behavioral', 'hard'),
                ('Cognizant', 'What interests you about working in IT services?', 'behavioral', 'easy'),
                ('Cognizant', 'Explain your experience with Agile methodologies.', 'technical', 'medium'),
                ('Cognizant', 'How do you ensure quality in software development?', 'technical', 'medium'),
                ('TCS', 'Why do you want to join TCS?', 'behavioral', 'easy'),
                ('TCS', 'Describe your experience with database management.', 'technical', 'medium'),
                ('TCS', 'How do you handle client escalations?', 'behavioral', 'hard'),
                ('Wipro', 'What are your strengths and weaknesses?', 'behavioral', 'easy'),
                ('Wipro', 'Explain your understanding of cloud computing.', 'technical', 'medium'),
                ('Wipro', 'How do you stay updated with new technologies?', 'behavioral', 'medium'),
                ('Microsoft', 'Why Microsoft?', 'behavioral', 'easy'),
                ('Microsoft', 'Explain the difference between process and thread.', 'technical', 'medium'),
                ('Microsoft', 'Design a scalable system for file storage.', 'technical', 'hard'),
                ('Google', 'Tell me about a challenging project you worked on.', 'behavioral', 'medium'),
                ('Google', 'How would you improve Google Search?', 'technical', 'hard'),
                ('Google', 'Explain how the internet works.', 'technical', 'medium')
            ]
            
            for company_name, question_text, q_type, difficulty in questions_data:
                company = Company.query.filter_by(name=company_name).first()
                question = Question(
                    company_id=company.id,
                    question_text=question_text,
                    question_type=q_type,
                    difficulty=difficulty
                )
                db.session.add(question)
            
            db.session.commit()
            print("Database initialized with companies and questions!")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)

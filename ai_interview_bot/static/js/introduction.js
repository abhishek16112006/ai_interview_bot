let recognition = null;

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('micBtnIntro').addEventListener('click', startRecording);
    document.getElementById('stopMicBtnIntro').addEventListener('click', stopRecording);
    document.getElementById('analyzeIntroBtn').addEventListener('click', analyzeIntroduction);
    document.getElementById('readTemplateBtn').addEventListener('click', readTemplate);
    
    const readExampleBtn = document.getElementById('readExampleBtn');
    if (readExampleBtn) {
        readExampleBtn.addEventListener('click', function() {
            const example = document.getElementById('professionalExample').textContent;
            speakText(example);
        });
    }
});

function readTemplate() {
    const template = `Hello, my name is [Your Name]. I am a [Your Role/Title] with [X years] of experience in [Your Field/Industry]. 
    I specialize in [Key Skills/Areas], and I have successfully [Major Achievement/Project]. 
    I'm passionate about [Your Interest], and I'm excited about the opportunity to [Goal/Aspiration].`;
    speakText(template);
}

function startRecording() {
    if (!recognition) {
        alert('Speech recognition is not supported in your browser. Please use Chrome.');
        return;
    }

    const introText = document.getElementById('introText');
    document.getElementById('micBtnIntro').disabled = true;
    document.getElementById('micBtnIntro').classList.add('recording');
    document.getElementById('stopMicBtnIntro').disabled = false;

    recognition.start();

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }

        introText.value = finalTranscript + interimTranscript;
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopRecording();
    };
}

function stopRecording() {
    if (recognition) {
        recognition.stop();
    }
    document.getElementById('micBtnIntro').disabled = false;
    document.getElementById('micBtnIntro').classList.remove('recording');
    document.getElementById('stopMicBtnIntro').disabled = true;
}

async function analyzeIntroduction() {
    const introText = document.getElementById('introText').value.trim();
    
    if (!introText || introText.length < 20) {
        alert('Please provide a more detailed introduction (at least 20 characters)');
        return;
    }

    const analyzeBtn = document.getElementById('analyzeIntroBtn');
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Analyzing...';

    try {
        const response = await fetch('/analyze_introduction', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ intro_text: introText })
        });

        const data = await response.json();

        if (data.success) {
            displayIntroFeedback(data);
        } else {
            alert(data.message || 'Error analyzing introduction');
        }
    } catch (error) {
        alert('Error analyzing introduction: ' + error.message);
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-brain me-1"></i> Analyze Introduction';
    }
}

function displayIntroFeedback(data) {
    document.getElementById('introScoreValue').textContent = Math.round(data.score);
    document.getElementById('introScoreBar').style.width = data.score + '%';
    
    if (data.score >= 80) {
        document.getElementById('introScoreBar').className = 'progress-bar bg-success';
    } else if (data.score >= 60) {
        document.getElementById('introScoreBar').className = 'progress-bar bg-warning';
    } else {
        document.getElementById('introScoreBar').className = 'progress-bar bg-danger';
    }

    document.getElementById('introFeedbackText').textContent = data.feedback;

    const strengthsList = document.getElementById('introStrengthsList');
    strengthsList.innerHTML = '';
    if (data.strengths && data.strengths.length > 0) {
        data.strengths.forEach(strength => {
            const li = document.createElement('li');
            li.textContent = strength;
            strengthsList.appendChild(li);
        });
    }

    const improvementsList = document.getElementById('introImprovementsList');
    improvementsList.innerHTML = '';
    if (data.improvements && data.improvements.length > 0) {
        data.improvements.forEach(improvement => {
            const li = document.createElement('li');
            li.textContent = improvement;
            improvementsList.appendChild(li);
        });
    }

    if (data.professional_example) {
        document.getElementById('professionalExample').textContent = data.professional_example;
    }

    document.getElementById('introFeedbackSection').classList.remove('d-none');
    document.getElementById('introFeedbackSection').scrollIntoView({ behavior: 'smooth' });
}

function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;
    window.speechSynthesis.speak(utterance);
}

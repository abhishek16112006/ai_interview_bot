let currentQuestionId = null;
let currentQuestionIndex = 0;
let totalQuestions = 0;
let recognition = null;

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    recognition = new SpeechRecognition();

    document.getElementById('analyzeBtn').addEventListener('click', analyzeAnswer);

    // currentQuestionIndex is 0-based in logic, but for progress we want tracking:
    // e.g. 0/5 -> 20% (started 1st question)
    const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100;
    document.getElementById('progressBar').style.width = progress + '%';
}

function startRecording() {
    if (!recognition) {
        alert('Speech recognition is not supported in your browser. Please use Chrome.');
        return;
    }

    const answerText = document.getElementById('answerText');
    document.getElementById('micBtn').disabled = true;
    document.getElementById('micBtn').classList.add('recording');
    document.getElementById('stopMicBtn').disabled = false;

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

        answerText.value = finalTranscript + interimTranscript;
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
    document.getElementById('micBtn').disabled = false;
    document.getElementById('micBtn').classList.remove('recording');
    document.getElementById('stopMicBtn').disabled = true;
}

async function analyzeAnswer() {
    const answerText = document.getElementById('answerText').value.trim();

    if (!answerText || answerText.length < 10) {
        alert('Please provide a more detailed answer (at least 10 characters)');
        return;
    }

    const analyzeBtn = document.getElementById('analyzeBtn');
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Analyzing...';

    try {
        const response = await fetch('/analyze_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: currentQuestionId,
                answer_text: answerText
            })
        });

        const data = await response.json();

        if (data.success) {
            displayFeedback(data);
        } else {
            alert(data.message || 'Error analyzing answer');
        }
    } catch (error) {
        alert('Error analyzing answer: ' + error.message);
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-brain me-1"></i> Analyze Answer';
    }
}

function displayFeedback(data) {
    document.getElementById('scoreValue').textContent = Math.round(data.score);
    document.getElementById('scoreBar').style.width = data.score + '%';

    if (data.score >= 80) {
        document.getElementById('scoreBar').className = 'progress-bar bg-success';
    } else if (data.score >= 60) {
        document.getElementById('scoreBar').className = 'progress-bar bg-warning';
    } else {
        document.getElementById('scoreBar').className = 'progress-bar bg-danger';
    }

    document.getElementById('feedbackText').textContent = data.feedback;

    const strengthsList = document.getElementById('strengthsList');
    strengthsList.innerHTML = '';
    if (data.strengths && data.strengths.length > 0) {
        data.strengths.forEach(strength => {
            const li = document.createElement('li');
            li.textContent = strength;
            strengthsList.appendChild(li);
        });
    } else {
        strengthsList.innerHTML = '<li>Keep practicing to identify strengths!</li>';
    }

    const improvementsList = document.getElementById('improvementsList');
    improvementsList.innerHTML = '';
    if (data.improvements && data.improvements.length > 0) {
        data.improvements.forEach(improvement => {
            const li = document.createElement('li');
            li.textContent = improvement;
            improvementsList.appendChild(li);
        });
    } else {
        improvementsList.innerHTML = '<li>Keep up the good work!</li>';
    }

    document.getElementById('feedbackSection').classList.remove('d-none');
    document.getElementById('feedbackSection').scrollIntoView({ behavior: 'smooth' });
}

function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;
    window.speechSynthesis.speak(utterance);
}

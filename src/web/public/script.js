let currentQuestionIndex = 0;
let questions = []; // learningPath questions currently loaded
let learningPaths = []
let learningPathQuestions = []
let title = ""

document.addEventListener('DOMContentLoaded', () => {
    fetch('questions.json')
        .then(response => response.json())
        .then(data => {
            console.log(data['certification_title'])
            title = data.certification_title;
            // take learning_pathh_title from data.questions
            data.questions.forEach(question => {
                learningPaths.push(question.learning_path_title);
                learningPathQuestions.push(question.questions);
            });
            buildLearningPathsMenu();
            
            //questions = data;
            showTitle();
            loadLearningPathQuestions(0);
        });
});

function buildLearningPathsMenu() {
    for (let i = 0; i < learningPaths.length; i++) {
        const learningPath = learningPaths[i];
        const learningPathElement = document.createElement('li');
        learningPathElement.classList.add('pure-menu-item');
        const link = document.createElement('a');
        link.classList.add('pure-menu-link');
        link.textContent = learningPath;
        link.href = '#';
        link.addEventListener('click', () => {
            event.preventDefault();
            // Remove the pure-menu-selected class from any previously selected link
            const previouslySelected = document.querySelector('.pure-menu-selected');
            if (previouslySelected) {
                previouslySelected.classList.remove('pure-menu-selected');
            }
            // Add the pure-menu-selected class to the clicked link
            learningPathElement.classList.add('pure-menu-selected');
            loadLearningPathQuestions(i);
        });
        learningPathElement.appendChild(link);
        document.getElementById('learning_path_ul').appendChild(learningPathElement);
    }
}

function showTitle() {
    document.getElementById('title').textContent = title;
}

function showLearningPath() {
    document.getElementById('learning_paths').textContent = title;
}

function showErrorMessage() {
    document.getElementById('error-message').style.display = 'block';
}
function hideErrorMessage() {
    document.getElementById('error-message').style.display = 'none';
}
function showCorrectAnswer() {
    document.getElementById('correct-answer').style.display = 'block';
}
function hideCorrectAnswer() {
    document.getElementById('correct-answer').style.display = 'none';
}
function showExplanation(explanation) {
    document.getElementById('explaination').textContent = explanation;
    document.getElementById('explaination').style.display = 'block';
}
function hideExplanation() {
    document.getElementById('explanation').style.display = 'none';
}

function loadLearningPathQuestions(learningPathIndex) {
    questions = learningPathQuestions[learningPathIndex];
    currentQuestionIndex = 0;
    refreshQuestion();
}

function refreshQuestion() {
    if (currentQuestionIndex >= questions.length) {
        document.getElementById('quiz-container').style.display = 'none';
        document.getElementById('result-container').style.display = 'block';
        return;
    }
    
    const question = questions[currentQuestionIndex];
    //hideExplanation();
    //hideCorrectAnswer();
    //hideErrorMessage();
    document.getElementById('question').textContent = question.question;
    
    const answersContainer = document.getElementById('answers');
    answersContainer.innerHTML = '';
    
    question.answers.forEach((answer, index) => {
        const radioInput = document.createElement('input');
        radioInput.type = 'radio';
        radioInput.name = 'answer';
        radioInput.id = `answer${index}`;
        radioInput.value = answer;

        const span = document.createElement('span');
        span.textContent = answer;
    
        const label = document.createElement('label');
        label.htmlFor = `answer${index}`;
        
        label.classList.add('pure-checkbox');
        label.appendChild(radioInput);
        label.appendChild(span);
        answersContainer.appendChild(label);
        radioInput.addEventListener('change', selectAnswer);
    });
}

function selectAnswer() {
    const selectedRadio = document.querySelector('input[name="answer"]:checked');
    if (!selectedRadio) {
        return true;
    }

    const selectedAnswer = selectedRadio.value;
    const question = questions[currentQuestionIndex];
    console.log(question);
    if (selectedAnswer === question.correct_answer) {
        showCorrectAnswer();
        showExplanation(question.explanation);
        hideErrorMessage();
    } else {
        showErrorMessage();
        hideCorrectAnswer();
    }
}
    
    function nextQuestion() {

            currentQuestionIndex++;
            refreshQuestion();
    }
    function prevQuestion() {
        if (currentQuestionIndex === 0) {
            return;
        }
        currentQuestionIndex++;
        refreshQuestion();
}
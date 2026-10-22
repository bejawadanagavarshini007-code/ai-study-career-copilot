/**
 * AI Study & Career Copilot — OptiMind Frontend Controller
 * Implements client-side state, closed-loop stage progression guards,
 * Practice stepper with instant completion resolution, Scenario Assignment
 * submission & validation, Dynamic Dark Curriculum Drawer, and Dashboard Analytics.
 */

// Application State
const state = {
  apiBase: '/api',
  currentTopic: 'Python Functions',
  currentDifficulty: 'Beginner',
  currentStage: 'dashboard',

  // Practice State (Stepper)
  practiceQuestions: [],
  currentPracticeIndex: 0,
  practiceSelections: {},     // { [qIdx]: selectedOption }
  practiceSubmitted: {},      // { [qIdx]: boolean }
  practiceCompleted: false,
  practiceCorrectCount: 0,

  // Assignment State
  assignmentSessionId: null,
  assignmentQuestions: [],
  assignmentAnswers: {},      // { [question_id]: selectedOption }
  assignmentSubmitted: false,
  assignmentResults: null,

  // Assessment State
  testSessionId: null,
  testQuestions: [],
  testAnswers: {},            // { [question_id]: selected_option }
  testSubmitted: false,
  lastResults: null,

  // Diagnostics & Personalization
  activeWeakConcept: null,
  targetedData: null
};

// ==========================================================================
// 1. NAVIGATION & PROGRESSION GUARDS
// ==========================================================================

function navigateTo(viewName) {
  // Progression Guard: Do not allow bypassing required submission steps
  if (viewName === 'assignment') {
    if (!state.practiceCompleted) {
      showToast('⚠️ Please complete all Practice questions before proceeding to Assignment.', true);
      viewName = 'practice';
    }
  } else if (viewName === 'test') {
    if (!state.practiceCompleted) {
      showToast('⚠️ Please complete Practice first.', true);
      viewName = 'practice';
    } else if (!state.assignmentSubmitted) {
      showToast('⚠️ Please submit your Assignment before proceeding to the Assessment.', true);
      viewName = 'assignment';
    }
  }

  state.currentStage = viewName;

  // Manage Container Visibility: Dashboard vs Stage Workspace
  const dashboardView = document.getElementById('view-dashboard');
  const stageWorkspace = document.getElementById('stage-workspace');
  const schedulePanel = document.getElementById('app-schedule-panel');

  if (viewName === 'dashboard') {
    if (dashboardView) {
      dashboardView.classList.add('active');
    }
    if (stageWorkspace) {
      stageWorkspace.classList.add('hidden');
    }
    if (schedulePanel) {
      schedulePanel.style.display = '';
    }
  } else {
    if (dashboardView) {
      dashboardView.classList.remove('active');
    }
    if (stageWorkspace) {
      stageWorkspace.classList.remove('hidden');
    }

    // Toggle active stage sub-view inside workspace
    document.querySelectorAll('.stage-content-area .view').forEach(view => {
      view.classList.remove('active');
    });

    const targetSubView = document.getElementById(`view-${viewName}`);
    if (targetSubView) {
      targetSubView.classList.add('active');
    }

    // Update Curriculum Drawer active stage & checkmarks
    updateCurriculumDrawer(viewName);
  }

  // Update Left Sidebar Nav Active State
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => {
    btn.classList.remove('active');
  });
  const activeNavBtn = document.getElementById(`nav-${viewName}`);
  if (activeNavBtn) {
    activeNavBtn.classList.add('active');
  }

  // Update Topbar and Sidebar Topic Pills
  updateTopicDisplays();

  // Lazy-load data when entering views
  if (viewName === 'learn') {
    if (!document.getElementById('learn-explanation').textContent.trim()) {
      fetchLearningContent(state.currentTopic, state.currentDifficulty);
    }
  } else if (viewName === 'practice') {
    if (state.practiceQuestions.length === 0) {
      loadPracticeQuestions();
    } else {
      renderCurrentPracticeQuestion();
    }
  } else if (viewName === 'assignment') {
    if (state.assignmentSubmitted && state.assignmentResults) {
      renderAssignmentResults(state.assignmentResults);
    } else if (state.assignmentQuestions.length === 0) {
      initiateAssignment();
    }
  } else if (viewName === 'test') {
    if (state.testQuestions.length === 0) {
      initiateTest();
    }
  } else if (viewName === 'progress' || viewName === 'dashboard') {
    loadProgress();
  }

  // Close mobile sidebar if open
  const sidebar = document.getElementById('app-sidebar');
  if (sidebar && sidebar.classList.contains('open')) {
    sidebar.classList.remove('open');
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateTopicDisplays() {
  const topbarTopic = document.getElementById('topbar-topic-label');
  const sidebarTopic = document.getElementById('sidebar-active-topic');
  const sidebarLevel = document.getElementById('sidebar-active-level');
  const drawerTopic = document.getElementById('drawer-topic-title');

  const text = `${state.currentTopic} • ${state.currentDifficulty}`;
  if (topbarTopic) topbarTopic.textContent = text;
  if (sidebarTopic) sidebarTopic.textContent = state.currentTopic;
  if (sidebarLevel) sidebarLevel.textContent = state.currentDifficulty;
  if (drawerTopic) drawerTopic.textContent = state.currentTopic;
}

// ==========================================================================
// 2. CURRICULUM DRAWER LOGIC (Matching Reference Image 2)
// ==========================================================================

function updateCurriculumDrawer(activeStage) {
  const stages = [
    { key: 'learn', label: '1. Concept Synthesis', isCompleted: true },
    { key: 'practice', label: '2. Guided Practice', isCompleted: state.practiceCompleted },
    { key: 'assignment', label: '3. Practical Assignment', isCompleted: state.assignmentSubmitted },
    { key: 'test', label: '4. Knowledge Evaluation', isCompleted: state.testSubmitted },
    { key: 'results', label: '5. Diagnostic Results', isCompleted: !!state.lastResults },
    { key: 'targeted', label: '6. Targeted Remediation', isCompleted: false }
  ];

  // Calculate dynamic progress percentage
  let completedCount = 0;
  if (activeStage === 'learn' || state.practiceQuestions.length > 0) completedCount = 1;
  if (state.practiceCompleted) completedCount = 2;
  if (state.assignmentSubmitted) completedCount = 3;
  if (state.testSubmitted) completedCount = 4;
  if (state.lastResults) completedCount = 5;

  const pct = Math.round((completedCount / stages.length) * 100);
  const progressBar = document.getElementById('drawer-progress-bar');
  const pctLabel = document.getElementById('drawer-pct-label');

  if (progressBar) progressBar.style.width = `${pct}%`;
  if (pctLabel) pctLabel.textContent = `${pct}% Completed`;

  // Update module items
  stages.forEach((st) => {
    const itemEl = document.getElementById(`curriculum-step-${st.key}`);
    const iconEl = document.getElementById(`step-icon-${st.key}`);

    if (itemEl) {
      itemEl.classList.remove('active', 'completed');

      if (st.key === activeStage) {
        itemEl.classList.add('active');
      }

      if (st.isCompleted) {
        itemEl.classList.add('completed');
        if (iconEl) iconEl.textContent = '✔';
      } else {
        if (iconEl) {
          if (st.key === 'learn') iconEl.textContent = '✔';
          else if (st.key === 'practice') iconEl.textContent = '⚡';
          else if (st.key === 'assignment') iconEl.textContent = '📝';
          else if (st.key === 'test') iconEl.textContent = '🎯';
          else if (st.key === 'results') iconEl.textContent = '📑';
          else if (st.key === 'targeted') iconEl.textContent = '🔍';
        }
      }
    }
  });
}

function toggleCurriculumDrawer() {
  const drawer = document.getElementById('curriculum-drawer');
  if (drawer) {
    drawer.classList.toggle('collapsed');
    const btn = drawer.querySelector('.drawer-toggle-btn');
    if (btn) {
      btn.textContent = drawer.classList.contains('collapsed') ? '☰ Show' : '☰ Hide';
    }
  }
}

function toggleSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  if (sidebar) {
    sidebar.classList.toggle('open');
  }
}

// Notification Toast
function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  if (!toast) return;

  toast.textContent = message;
  toast.className = `toast ${isError ? 'text-danger' : ''}`;
  toast.classList.remove('hidden');

  setTimeout(() => {
    toast.classList.add('hidden');
  }, 4000);
}

// Quick Search
function quickSearchTopic(term) {
  if (!term || !term.trim()) return;
  document.getElementById('topic-input').value = term.trim();
  handleStartLearning();
}

// ==========================================================================
// 3. DASHBOARD ACTIONS
// ==========================================================================

function quickSelect(topic, level) {
  const topicInput = document.getElementById('topic-input');
  const diffSelect = document.getElementById('difficulty-select');

  if (topicInput) topicInput.value = topic;
  if (diffSelect) diffSelect.value = level;
  handleStartLearning();
}

async function handleStartLearning(event) {
  if (event) event.preventDefault();

  const topicInput = document.getElementById('topic-input');
  const diffSelect = document.getElementById('difficulty-select');

  const topic = (topicInput ? topicInput.value.trim() : '') || 'Python Functions';
  const difficulty = (diffSelect ? diffSelect.value : '') || 'Beginner';

  if (topic !== state.currentTopic || difficulty !== state.currentDifficulty) {
    state.currentTopic = topic;
    state.currentDifficulty = difficulty;
    resetFlowState();
  }

  navigateTo('learn');
  await fetchLearningContent(topic, difficulty);
}

function resetFlowState() {
  state.practiceQuestions = [];
  state.currentPracticeIndex = 0;
  state.practiceSelections = {};
  state.practiceSubmitted = {};
  state.practiceCompleted = false;
  state.practiceCorrectCount = 0;

  state.assignmentSessionId = null;
  state.assignmentQuestions = [];
  state.assignmentAnswers = {};
  state.assignmentSubmitted = false;
  state.assignmentResults = null;

  state.testSessionId = null;
  state.testQuestions = [];
  state.testAnswers = {};
  state.testSubmitted = false;
  state.lastResults = null;
  state.activeWeakConcept = null;
  state.targetedData = null;
}

// ==========================================================================
// 4. STAGE 1: LEARN (CONCEPT SYNTHESIS)
// ==========================================================================

async function fetchLearningContent(topic, difficulty) {
  const loading = document.getElementById('learn-loading');
  const content = document.getElementById('learn-content');
  const topicTitle = document.getElementById('learn-topic-title');

  if (topicTitle) topicTitle.textContent = `${topic} — ${difficulty}`;
  if (loading) loading.classList.remove('hidden');
  if (content) content.classList.add('hidden');

  try {
    const res = await fetch(`${state.apiBase}/learn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, level: difficulty })
    });

    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();
    renderLearningContent(data);
  } catch (err) {
    console.error('Error fetching learning content:', err);
    showToast('Failed to load topic synthesis. Using local overview.', true);
    renderLearningFallback(topic, difficulty);
  } finally {
    if (loading) loading.classList.add('hidden');
    if (content) content.classList.remove('hidden');
  }
}

function renderLearningContent(data) {
  const explanationBox = document.getElementById('learn-explanation');
  const keyPointsList = document.getElementById('learn-key-points');
  const examplesBox = document.getElementById('learn-examples');

  if (explanationBox) {
    explanationBox.innerHTML = `<p>${escapeHTML(data.explanation || 'No explanation provided.')}</p>`;
  }

  if (keyPointsList) {
    keyPointsList.innerHTML = '';
    (data.key_points || []).forEach(pt => {
      const li = document.createElement('li');
      li.textContent = pt;
      keyPointsList.appendChild(li);
    });
  }

  if (examplesBox) {
    examplesBox.innerHTML = '';
    (data.examples || []).forEach(ex => {
      const div = document.createElement('div');
      div.className = 'example-card';
      div.innerHTML = `
        <h4>${escapeHTML(ex.title || 'Code Example')}</h4>
        <pre><code>${escapeHTML(ex.code || ex.content || '')}</code></pre>
        <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 0.5rem;">${escapeHTML(ex.notes || '')}</p>
      `;
      examplesBox.appendChild(div);
    });
  }
}

function renderLearningFallback(topic, difficulty) {
  renderLearningContent({
    explanation: `${topic} is a core foundation of modern software engineering. Mastering its semantics, parameters, and return patterns ensures modular and scalable architectures.`,
    key_points: [
      `Structure, syntax, and proper execution scope of ${topic}.`,
      `Handling inputs, return types, and side effects deterministically.`,
      `Edge cases, guard clauses, and error boundary patterns.`
    ],
    examples: [
      {
        title: `Standard ${topic} Pattern`,
        code: `# Demonstration of ${topic} pattern\ndef execute_task(value: int) -> int:\n    """Calculates deterministic transformation."""\n    return value * 2\n\nresult = execute_task(21)\nprint(result) # Output: 42`,
        notes: `Emphasizes pure logic, clear typing, and high testability.`
      }
    ]
  });
}

function proceedToPractice() {
  navigateTo('practice');
}

// ==========================================================================
// 5. STAGE 2: PRACTICE (INTERACTIVE STEPPER & RESOLUTION)
// Resolves the issue where practice was stuck on the last question's feedback!
// ==========================================================================

async function loadPracticeQuestions() {
  const loading = document.getElementById('practice-loading');
  const container = document.getElementById('practice-container');
  const topicTitle = document.getElementById('practice-topic-title');
  const completionCard = document.getElementById('practice-completion-card');
  const stepperBar = document.getElementById('practice-stepper-bar');

  if (topicTitle) topicTitle.textContent = `${state.currentTopic} Practice`;
  if (container) container.innerHTML = '';
  if (completionCard) completionCard.classList.add('hidden');
  if (stepperBar) stepperBar.classList.remove('hidden');
  if (loading) loading.classList.remove('hidden');

  try {
    const res = await fetch(`${state.apiBase}/practice`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: state.currentTopic, level: state.currentDifficulty })
    });

    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();
    state.practiceQuestions = data.questions || [];
    state.currentPracticeIndex = 0;
    state.practiceSelections = {};
    state.practiceSubmitted = {};
    state.practiceCompleted = false;
    state.practiceCorrectCount = 0;

    renderCurrentPracticeQuestion();
  } catch (err) {
    console.error('Error fetching practice questions:', err);
    showToast('Failed to load practice questions.', true);
  } finally {
    if (loading) loading.classList.add('hidden');
  }
}

function renderCurrentPracticeQuestion() {
  const container = document.getElementById('practice-container');
  const completionCard = document.getElementById('practice-completion-card');
  const stepperBar = document.getElementById('practice-stepper-bar');
  const stepperText = document.getElementById('practice-stepper-text');
  const stepperFill = document.getElementById('practice-stepper-fill');

  if (!container) return;

  const total = state.practiceQuestions.length;

  // If already completed and user navigates back, show completion card directly
  if (state.practiceCompleted && state.currentPracticeIndex >= total) {
    showPracticeCompletion();
    return;
  }

  if (total === 0) {
    container.innerHTML = `<p style="color: var(--text-muted); padding: 2rem;">No practice questions loaded. Click restart above.</p>`;
    return;
  }

  // Ensure valid index
  if (state.currentPracticeIndex >= total) {
    state.currentPracticeIndex = total - 1;
  }

  const idx = state.currentPracticeIndex;
  const q = state.practiceQuestions[idx];

  // Update Stepper Bar
  if (stepperBar) stepperBar.classList.remove('hidden');
  if (completionCard) completionCard.classList.add('hidden');
  if (container) container.classList.remove('hidden');

  if (stepperText) stepperText.textContent = `Question ${idx + 1} of ${total}`;
  if (stepperFill) stepperFill.style.width = `${Math.round(((idx + 1) / total) * 100)}%`;

  const isSubmitted = !!state.practiceSubmitted[idx];
  const userSelected = state.practiceSelections[idx];
  const isCorrect = isSubmitted && (userSelected === q.correct_answer);

  // Render Question Options Pills (Image 2 style)
  const optionsHtml = (q.options || []).map((opt, optIdx) => {
    const char = String.fromCharCode(65 + optIdx);
    const isThisSelected = userSelected === opt;
    let btnClasses = ['option-btn'];

    if (isThisSelected) btnClasses.push('selected');
    if (isSubmitted) {
      if (opt === q.correct_answer) {
        btnClasses.push('correct');
      } else if (isThisSelected) {
        btnClasses.push('incorrect');
      }
    }

    return `
      <button 
        type="button" 
        class="${btnClasses.join(' ')}" 
        ${isSubmitted ? 'disabled' : ''} 
        onclick="selectPracticeOption(${idx}, '${escapeQuotes(opt)}', this)">
        <span class="option-indicator">${char}</span>
        <span>${escapeHTML(opt)}</span>
      </button>
    `;
  }).join('');

  // Determine button state: Submit vs Next vs View Summary
  let actionButtonsHtml = '';
  const isLastQuestion = (idx === total - 1);

  if (!isSubmitted) {
    actionButtonsHtml = `
      <button class="btn btn-primary btn-large" id="btn-submit-practice" onclick="submitPracticeAnswer(${idx})">
        Submit Answer
      </button>
    `;
  } else {
    if (!isLastQuestion) {
      actionButtonsHtml = `
        <button class="btn btn-primary btn-large" onclick="advancePracticeStepper()">
          Next Question →
        </button>
      `;
    } else {
      actionButtonsHtml = `
        <button class="btn btn-primary btn-large" style="background: var(--accent-purple);" onclick="showPracticeCompletion()">
          View Practice Summary 🎉 →
        </button>
      `;
    }
  }

  container.innerHTML = `
    <div class="question-card" id="active-practice-card">
      <div class="question-header">
        <span class="concept-tag">${escapeHTML(q.concept || 'Concept Drill')}</span>
        <span class="quiz-pill-badge">✔ Quiz ${idx + 1}</span>
      </div>

      <div class="question-text">${escapeHTML(q.question)}</div>

      <div class="options-grid">
        ${optionsHtml}
      </div>

      <!-- Feedback (Matching Image 2) -->
      ${isSubmitted ? `
        <div class="your-answer-line" style="color: ${isCorrect ? 'var(--success-text)' : 'var(--danger-text)'}">
          Your answer: ${escapeHTML(userSelected || 'None')} ${isCorrect ? '✔' : '✖'}
        </div>
        <div class="practice-feedback show ${isCorrect ? 'correct' : 'incorrect'}">
          <strong>${isCorrect ? '✔ Correct Answer!' : '✖ Needs Attention.'}</strong><br>
          ${!isCorrect ? `The correct answer is: <em>${escapeHTML(q.correct_answer)}</em>.<br>` : ''}
          ${escapeHTML(q.explanation || '')}
        </div>
        ${q.hint ? `
          <div class="practice-hint">
            <span>💡 <strong>Hint:</strong> ${escapeHTML(q.hint)}</span>
          </div>
        ` : ''}
      ` : ''}

      <div class="practice-actions">
        ${actionButtonsHtml}
        ${idx > 0 ? `
          <button class="btn btn-outline" onclick="previousPracticeStepper()">
            ← Previous Question
          </button>
        ` : ''}
      </div>
    </div>
  `;
}

function selectPracticeOption(qIdx, selectedOption, btn) {
  if (state.practiceSubmitted[qIdx]) return;

  state.practiceSelections[qIdx] = selectedOption;

  const card = document.getElementById('active-practice-card');
  if (card) {
    card.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
  }
  btn.classList.add('selected');
}

function submitPracticeAnswer(qIdx) {
  if (state.practiceSubmitted[qIdx]) return;

  const selectedOption = state.practiceSelections[qIdx];
  if (!selectedOption) {
    showToast('⚠️ Please select an option before submitting.', true);
    return;
  }

  const q = state.practiceQuestions[qIdx];
  state.practiceSubmitted[qIdx] = true;
  const isCorrect = (selectedOption === q.correct_answer);

  if (isCorrect) {
    state.practiceCorrectCount++;
  }

  // Check if all questions are now submitted
  const total = state.practiceQuestions.length;
  const submittedCount = Object.keys(state.practiceSubmitted).length;
  if (submittedCount === total) {
    state.practiceCompleted = true;
    updateCurriculumDrawer('practice');
  }

  // Re-render question with feedback & next button
  renderCurrentPracticeQuestion();
}

function advancePracticeStepper() {
  if (state.currentPracticeIndex < state.practiceQuestions.length - 1) {
    state.currentPracticeIndex++;
    renderCurrentPracticeQuestion();
  } else {
    showPracticeCompletion();
  }
}

function previousPracticeStepper() {
  if (state.currentPracticeIndex > 0) {
    state.currentPracticeIndex--;
    renderCurrentPracticeQuestion();
  }
}

function showPracticeCompletion() {
  state.practiceCompleted = true;
  updateCurriculumDrawer('practice');

  const container = document.getElementById('practice-container');
  const stepperBar = document.getElementById('practice-stepper-bar');
  const completionCard = document.getElementById('practice-completion-card');
  const compStats = document.getElementById('practice-completion-stats');
  const compMsg = document.getElementById('practice-completion-message');

  if (container) container.classList.add('hidden');
  if (stepperBar) stepperBar.classList.add('hidden');
  if (completionCard) completionCard.classList.remove('hidden');

  const total = state.practiceQuestions.length;
  if (compStats) {
    compStats.textContent = `${state.practiceCorrectCount} of ${total} Questions Answered Correctly`;
  }
  if (compMsg) {
    compMsg.textContent = `Outstanding! You have thoroughly completed all interactive drills for ${state.currentTopic}. Your conceptual foundation is set for the applied Assignment.`;
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function restartPractice() {
  state.practiceSelections = {};
  state.practiceSubmitted = {};
  state.practiceCorrectCount = 0;
  state.currentPracticeIndex = 0;
  state.practiceCompleted = false;

  const completionCard = document.getElementById('practice-completion-card');
  const container = document.getElementById('practice-container');
  const stepperBar = document.getElementById('practice-stepper-bar');

  if (completionCard) completionCard.classList.add('hidden');
  if (container) container.classList.remove('hidden');
  if (stepperBar) stepperBar.classList.remove('hidden');

  renderCurrentPracticeQuestion();
}

function proceedToAssignment() {
  if (!state.practiceCompleted) {
    showToast('⚠️ Please finish practice questions before proceeding.', true);
    return;
  }
  navigateTo('assignment');
}

// ==========================================================================
// 6. STAGE 3: ASSIGNMENT (SCENARIOS & VALIDATION)
// ==========================================================================

async function initiateAssignment() {
  const loading = document.getElementById('assignment-loading');
  const container = document.getElementById('assignment-questions-container');
  const topicTitle = document.getElementById('assignment-topic-title');
  const assignTitle = document.getElementById('assignment-title');
  const assignInstr = document.getElementById('assignment-instructions');
  const resultsCard = document.getElementById('assignment-results-container');
  const submitBtn = document.getElementById('btn-submit-assignment');

  if (topicTitle) topicTitle.textContent = `${state.currentTopic} Practical Assignment`;
  if (container) container.innerHTML = '';
  if (resultsCard) resultsCard.classList.add('hidden');
  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Submit Assignment';
  }
  if (loading) loading.classList.remove('hidden');

  try {
    const res = await fetch(`${state.apiBase}/assignment/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: state.currentTopic, level: state.currentDifficulty })
    });

    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();

    state.assignmentSessionId = data.session_id;
    state.assignmentQuestions = data.questions || [];
    if (assignTitle) assignTitle.textContent = data.title || `${state.currentTopic} Practical Assignment`;
    if (assignInstr) assignInstr.textContent = data.instructions || 'Analyze each production scenario and choose the most robust engineering solution.';

    renderAssignmentQuestions(state.assignmentQuestions);
  } catch (err) {
    console.error('Error generating assignment:', err);
    showToast('Failed to generate assignment. Please try again.', true);
  } finally {
    if (loading) loading.classList.add('hidden');
  }
}

function renderAssignmentQuestions(questions) {
  const container = document.getElementById('assignment-questions-container');
  if (!container) return;
  container.innerHTML = '';

  if (!questions || questions.length === 0) {
    container.innerHTML = `<p style="color: var(--text-muted);">No assignment questions available.</p>`;
    return;
  }

  questions.forEach((q, idx) => {
    const card = document.createElement('div');
    card.className = 'question-card';
    card.id = `assignment-q-${q.question_id}`;

    const optionsHtml = (q.options || []).map((opt, optIdx) => {
      const char = String.fromCharCode(65 + optIdx);
      const isSelected = state.assignmentAnswers[q.question_id] === opt;
      const isSubmitted = state.assignmentSubmitted;

      return `
        <button 
          type="button"
          class="option-btn ${isSelected ? 'selected' : ''}" 
          id="assignment-opt-${q.question_id}-${optIdx}" 
          ${isSubmitted ? 'disabled' : ''}
          onclick="selectAssignmentOption(${q.question_id}, '${escapeQuotes(opt)}', this)">
          <span class="option-indicator">${char}</span>
          <span>${escapeHTML(opt)}</span>
        </button>
      `;
    }).join('');

    card.innerHTML = `
      <div class="question-header">
        <span class="concept-tag">${escapeHTML(q.concept || 'Production Scenario')}</span>
        <span style="font-size: 0.82rem; color: var(--text-dim); font-weight: 600;">Scenario ${idx + 1} of ${questions.length}</span>
      </div>
      <div class="question-text">${escapeHTML(q.question)}</div>
      <div class="options-grid">
        ${optionsHtml}
      </div>
      ${q.hint ? `
        <div class="practice-hint" style="margin-top: 1rem;">
          <span>💡 <strong>Scenario Hint:</strong> ${escapeHTML(q.hint)}</span>
        </div>
      ` : ''}
    `;

    container.appendChild(card);
  });
}

function selectAssignmentOption(questionId, selectedOption, btn) {
  if (state.assignmentSubmitted) return;

  state.assignmentAnswers[questionId] = selectedOption;

  const card = document.getElementById(`assignment-q-${questionId}`);
  if (card) {
    card.classList.remove('unanswered-error');
    card.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
  }
  btn.classList.add('selected');
}

async function submitAssignment() {
  if (state.assignmentSubmitted) {
    showToast('Assignment has already been submitted.');
    return;
  }

  // 1. Validate required answers
  let missing = false;
  state.assignmentQuestions.forEach(q => {
    if (!state.assignmentAnswers[q.question_id] || !state.assignmentAnswers[q.question_id].trim()) {
      missing = true;
      const card = document.getElementById(`assignment-q-${q.question_id}`);
      if (card) card.classList.add('unanswered-error');
    }
  });

  if (missing) {
    showToast('⚠️ Please answer all required assignment questions before submitting.', true);
    const firstErr = document.querySelector('.question-card.unanswered-error');
    if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }

  const submitBtn = document.getElementById('btn-submit-assignment');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Evaluating Assignment...';
  }

  try {
    const payload = {
      session_id: state.assignmentSessionId,
      topic: state.currentTopic,
      level: state.currentDifficulty,
      answers: state.assignmentAnswers
    };

    const res = await fetch(`${state.apiBase}/assignment/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const result = await res.json();

    state.assignmentSubmitted = true;
    state.assignmentResults = result;

    renderAssignmentResults(result);
    updateCurriculumDrawer('assignment');
    showToast('🎉 Assignment submitted and evaluated successfully!');
  } catch (err) {
    console.error('Error submitting assignment:', err);
    showToast('Failed to evaluate assignment. Please try again.', true);
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Assignment';
    }
  }
}

function renderAssignmentResults(result) {
  const resultsCard = document.getElementById('assignment-results-container');
  const percentEl = document.getElementById('assignment-score-percent');
  const fractionEl = document.getElementById('assignment-score-fraction');
  const circleEl = document.getElementById('assignment-score-circle');
  const verdictEl = document.getElementById('assignment-score-verdict');
  const feedbackEl = document.getElementById('assignment-feedback-text');
  const reviewContainer = document.getElementById('assignment-review-container');
  const headerNextBtn = document.getElementById('btn-assignment-next');
  const submitBtn = document.getElementById('btn-submit-assignment');

  // Disable options and submit button to prevent accidental duplicate submission
  document.querySelectorAll('#assignment-questions-container .option-btn').forEach(b => {
    b.disabled = true;
  });
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Assignment Evaluated ✔';
  }

  if (headerNextBtn) headerNextBtn.classList.remove('hidden');

  const pct = Math.round(result.score_percentage || 0);
  if (percentEl) percentEl.textContent = `${pct}%`;
  if (fractionEl) fractionEl.textContent = `${result.correct_count} / ${result.total_questions} Correct`;

  if (circleEl) {
    if (pct >= 80) {
      circleEl.style.borderColor = 'var(--success)';
      percentEl.style.color = 'var(--success-text)';
      if (verdictEl) verdictEl.textContent = 'Applied Scenario Mastery! 🌟';
    } else if (pct >= 60) {
      circleEl.style.borderColor = 'var(--warning)';
      percentEl.style.color = 'var(--warning-text)';
      if (verdictEl) verdictEl.textContent = 'Solid Engineering Intuition 👍';
    } else {
      circleEl.style.borderColor = 'var(--danger)';
      percentEl.style.color = 'var(--danger-text)';
      if (verdictEl) verdictEl.textContent = 'Needs Scenario Practice 🎯';
    }
  }

  if (feedbackEl) {
    feedbackEl.textContent = result.feedback || 'Assignment evaluation completed.';
  }

  // Render Question Reviews (Matching Image 2 style)
  if (reviewContainer) {
    reviewContainer.innerHTML = '';
    (result.question_review || []).forEach((r, rIdx) => {
      const card = document.createElement('div');
      card.className = 'question-card';
      const isCorr = r.is_correct;

      card.innerHTML = `
        <div class="question-header">
          <span class="concept-tag">${escapeHTML(r.concept || 'Scenario Review')}</span>
          <span style="font-weight: 700; color: ${isCorr ? 'var(--success-text)' : 'var(--danger-text)'}">
            ${isCorr ? '✔ Correct' : '✖ Incorrect'}
          </span>
        </div>
        <div class="question-text">${escapeHTML(r.question)}</div>
        <div class="your-answer-line" style="color: ${isCorr ? 'var(--success-text)' : 'var(--danger-text)'}">
          Your answer: ${escapeHTML(r.user_answer || 'Not answered')}
        </div>
        ${!isCorr ? `
          <div style="font-size: 0.9rem; font-weight: 600; color: var(--success-text); margin-bottom: 0.5rem;">
            Correct answer: ${escapeHTML(r.correct_answer)}
          </div>
        ` : ''}
        <div class="practice-feedback show ${isCorr ? 'correct' : 'incorrect'}">
          ${escapeHTML(r.explanation || '')}
        </div>
      `;
      reviewContainer.appendChild(card);
    });
  }

  if (resultsCard) {
    resultsCard.classList.remove('hidden');
    resultsCard.scrollIntoView({ behavior: 'smooth' });
  }
}

function proceedToAssessment() {
  if (!state.assignmentSubmitted) {
    showToast('⚠️ Please submit your assignment before proceeding to the assessment.', true);
    return;
  }
  navigateTo('test');
}

// ==========================================================================
// 7. STAGE 4: ASSESSMENT (SCORED EVALUATION)
// ==========================================================================

async function initiateTest() {
  const loading = document.getElementById('test-loading');
  const container = document.getElementById('test-questions-container');
  const topicTitle = document.getElementById('test-topic-title');
  const progressBadge = document.getElementById('test-progress-indicator');

  if (topicTitle) topicTitle.textContent = `${state.currentTopic} Assessment`;
  if (container) container.innerHTML = '';
  state.testAnswers = {};
  state.testSessionId = null;
  state.testSubmitted = false;
  if (loading) loading.classList.remove('hidden');

  try {
    const res = await fetch(`${state.apiBase}/test/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: state.currentTopic, level: state.currentDifficulty })
    });

    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();

    state.testSessionId = data.session_id;
    state.testQuestions = data.questions || [];

    if (progressBadge) progressBadge.textContent = `${state.testQuestions.length} Questions`;
    renderTestQuestions(state.testQuestions);
  } catch (err) {
    console.error('Error generating assessment:', err);
    showToast('Failed to generate assessment. Please try again.', true);
  } finally {
    if (loading) loading.classList.add('hidden');
  }
}

function renderTestQuestions(questions) {
  const container = document.getElementById('test-questions-container');
  if (!container) return;
  container.innerHTML = '';

  if (!questions || questions.length === 0) {
    container.innerHTML = `<p style="color: var(--text-muted);">Could not load assessment questions.</p>`;
    return;
  }

  questions.forEach((q, idx) => {
    const card = document.createElement('div');
    card.className = 'question-card';
    card.id = `test-q-card-${q.question_id}`;

    const optionsHtml = (q.options || []).map((opt, optIdx) => {
      const char = String.fromCharCode(65 + optIdx);
      const isSelected = state.testAnswers[q.question_id] === opt;
      return `
        <button 
          type="button"
          class="option-btn ${isSelected ? 'selected' : ''}" 
          id="test-opt-${q.question_id}-${optIdx}" 
          onclick="selectTestOption(${q.question_id}, '${escapeQuotes(opt)}', this)">
          <span class="option-indicator">${char}</span>
          <span>${escapeHTML(opt)}</span>
        </button>
      `;
    }).join('');

    card.innerHTML = `
      <div class="question-header">
        <span class="concept-tag">${escapeHTML(q.concept || 'General')}</span>
        <span style="font-size: 0.8rem; color: var(--text-dim); font-weight: 600;">Question ${idx + 1} of ${questions.length}</span>
      </div>
      <div class="question-text">${escapeHTML(q.question)}</div>
      <div class="options-grid">
        ${optionsHtml}
      </div>
    `;

    container.appendChild(card);
  });
}

function selectTestOption(questionId, selectedOption, btn) {
  state.testAnswers[questionId] = selectedOption;

  const card = document.getElementById(`test-q-card-${questionId}`);
  if (card) {
    card.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
  }
  btn.classList.add('selected');
}

async function submitAssessment() {
  const totalQuestions = state.testQuestions.length;
  const answeredCount = Object.keys(state.testAnswers).length;

  if (answeredCount < totalQuestions) {
    const proceed = confirm(`You have answered ${answeredCount} of ${totalQuestions} questions. Do you still wish to submit for evaluation?`);
    if (!proceed) return;
  }

  const submitBtn = document.getElementById('btn-submit-test');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting & Evaluating with AI...';
  }

  try {
    const payload = {
      session_id: state.testSessionId,
      topic: state.currentTopic,
      level: state.currentDifficulty,
      answers: state.testAnswers
    };

    const res = await fetch(`${state.apiBase}/test/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);

    const result = await res.json();
    state.lastResults = result;
    state.testSubmitted = true;

    renderResults(result);
    navigateTo('results');
    showToast('🎉 Assessment evaluated successfully!');
  } catch (err) {
    console.error('Error submitting assessment:', err);
    showToast('Failed to evaluate assessment. Check backend connection.', true);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Assessment for AI Evaluation';
    }
  }
}

// ==========================================================================
// 8. STAGE 5: RESULTS & DIAGNOSTICS
// ==========================================================================

function renderResults(result) {
  const percentEl = document.getElementById('results-score-percent');
  const fractionEl = document.getElementById('results-score-fraction');
  const verdictEl = document.getElementById('results-verdict');
  const summaryEl = document.getElementById('results-summary');
  const circleEl = document.getElementById('score-circle');

  const pct = Math.round(result.score_percentage || 0);
  if (percentEl) percentEl.textContent = `${pct}%`;
  if (fractionEl) fractionEl.textContent = `${result.correct_count} / ${result.total_questions} Correct`;

  if (circleEl) {
    if (pct >= 80) {
      circleEl.style.borderColor = 'var(--success)';
      percentEl.style.color = 'var(--success-text)';
      if (verdictEl) verdictEl.textContent = 'Excellent Mastery! 🌟';
    } else if (pct >= 60) {
      circleEl.style.borderColor = 'var(--warning)';
      percentEl.style.color = 'var(--warning-text)';
      if (verdictEl) verdictEl.textContent = 'Good Effort — Reinforce Weak Spots 👍';
    } else {
      circleEl.style.borderColor = 'var(--danger)';
      percentEl.style.color = 'var(--danger-text)';
      if (verdictEl) verdictEl.textContent = 'Needs Focused Practice 🎯';
    }
  }

  if (summaryEl) {
    summaryEl.textContent = result.summary || `You completed the ${state.currentTopic} assessment.`;
  }

  // Concept-by-Concept breakdown
  const conceptContainer = document.getElementById('concept-analysis-list');
  if (conceptContainer) {
    conceptContainer.innerHTML = '';
    (result.concept_analysis || []).forEach(c => {
      const row = document.createElement('div');
      row.className = 'concept-row';
      const isWeak = c.status === 'Needs Practice' || c.accuracy < 60;
      row.innerHTML = `
        <div>
          <strong>${escapeHTML(c.concept)}</strong>
          <div style="font-size: 0.78rem; color: var(--text-dim);">${c.correct}/${c.total} Correct (${Math.round(c.accuracy)}%)</div>
        </div>
        <span class="concept-status-badge ${isWeak ? 'status-weak' : 'status-mastered'}">
          ${isWeak ? 'Needs Practice ⚠️' : 'Strong Concept ✔'}
        </span>
      `;
      conceptContainer.appendChild(row);
    });
  }

  // Weak Concept Remediation Banner
  const weakBanner = document.getElementById('weak-concepts-banner');
  const weakText = document.getElementById('weak-concepts-text');
  const weakConcepts = result.weak_concepts || [];

  if (weakConcepts.length > 0) {
    state.activeWeakConcept = weakConcepts[0];
    if (weakBanner) weakBanner.classList.remove('hidden');
    if (weakText) weakText.textContent = `Identified knowledge gaps: "${weakConcepts.join(', ')}". Click below to practice the targeted drill.`;
  } else {
    state.activeWeakConcept = null;
    if (weakBanner) weakBanner.classList.add('hidden');
  }

  // Question-by-Question Review (Image 2 style)
  renderReviewQuestions(result.question_review || []);
}

function renderReviewQuestions(reviews) {
  const container = document.getElementById('results-question-review');
  if (!container) return;
  container.innerHTML = '';

  reviews.forEach(r => {
    const card = document.createElement('div');
    card.className = 'question-card';
    const isCorrect = r.is_correct;

    card.innerHTML = `
      <div class="question-header">
        <span class="concept-tag">${escapeHTML(r.concept || 'Concept Review')}</span>
        <span style="font-weight: 700; color: ${isCorrect ? 'var(--success-text)' : 'var(--danger-text)'}">
          ${isCorrect ? '✔ Correct' : '✖ Incorrect'}
        </span>
      </div>
      <div class="question-text">${escapeHTML(r.question)}</div>
      <div class="your-answer-line" style="color: ${isCorrect ? 'var(--success-text)' : 'var(--danger-text)'}">
        Your answer: ${escapeHTML(r.user_answer || 'Not answered')}
      </div>
      ${!isCorrect ? `
        <div style="font-size: 0.9rem; font-weight: 600; color: var(--success-text); margin-bottom: 0.5rem;">
          Correct answer: ${escapeHTML(r.correct_answer)}
        </div>
      ` : ''}
      <div class="practice-feedback show ${isCorrect ? 'correct' : 'incorrect'}">
        ${escapeHTML(r.explanation || 'Review the conceptual model above.')}
      </div>
    `;
    container.appendChild(card);
  });
}

// ==========================================================================
// 9. STAGE 6: TARGETED REMEDIATION
// ==========================================================================

async function startTargetedPractice() {
  const concept = state.activeWeakConcept || (state.lastResults && state.lastResults.weak_concepts && state.lastResults.weak_concepts[0]);
  if (!concept) {
    showToast('No weak concept identified to practice.');
    return;
  }

  navigateTo('targeted');

  const loading = document.getElementById('targeted-loading');
  const content = document.getElementById('targeted-content');
  const titleEl = document.getElementById('targeted-concept-title');

  if (titleEl) titleEl.textContent = `Targeted Remediation: ${concept}`;
  if (loading) loading.classList.remove('hidden');
  if (content) content.classList.add('hidden');

  try {
    const res = await fetch(`${state.apiBase}/targeted-practice`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: state.currentTopic,
        weak_concept: concept,
        level: state.currentDifficulty
      })
    });

    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);

    const data = await res.json();
    state.targetedData = data;
    renderTargetedContent(data);
  } catch (err) {
    console.error('Error fetching targeted practice:', err);
    showToast('Failed to load targeted drill.', true);
  } finally {
    if (loading) loading.classList.add('hidden');
    if (content) content.classList.remove('hidden');
  }
}

function renderTargetedContent(data) {
  const explBox = document.getElementById('targeted-explanation');
  const exampleBox = document.getElementById('targeted-example');
  const drillBox = document.getElementById('targeted-drill-container');

  if (explBox) {
    explBox.innerHTML = `
      <h3 style="color: var(--warning-text); margin-bottom: 0.5rem;">Why is this concept tricky?</h3>
      <p>${escapeHTML(data.explanation || 'Here is a focused breakdown of this concept.')}</p>
    `;
  }

  if (exampleBox) {
    exampleBox.innerHTML = `
      <h4 style="margin: 0.5rem 0; font-size: 0.95rem;">${escapeHTML(data.example_title || 'Targeted Code Pattern')}</h4>
      <pre><code>${escapeHTML(data.example_code || '')}</code></pre>
      <p style="font-size: 0.88rem; color: var(--text-muted);">${escapeHTML(data.example_notes || '')}</p>
    `;
  }

  if (drillBox && data.drill_question) {
    const q = data.drill_question;
    const optionsHtml = (q.options || []).map((opt, optIdx) => {
      const char = String.fromCharCode(65 + optIdx);
      return `
        <button 
          type="button"
          class="option-btn" 
          onclick="checkTargetedDrill('${escapeQuotes(opt)}', '${escapeQuotes(q.correct_answer)}', '${escapeQuotes(q.explanation || '')}', this)">
          <span class="option-indicator">${char}</span>
          <span>${escapeHTML(opt)}</span>
        </button>
      `;
    }).join('');

    drillBox.innerHTML = `
      <div class="question-card">
        <div class="question-header">
          <span class="concept-tag">${escapeHTML(state.activeWeakConcept || 'Remedial Drill')}</span>
          <span style="font-size: 0.8rem; color: var(--text-dim); font-weight: 600;">Reinforcement Question</span>
        </div>
        <div class="question-text">${escapeHTML(q.question)}</div>
        <div class="options-grid">${optionsHtml}</div>
        <div class="practice-feedback" id="targeted-drill-feedback"></div>
      </div>
    `;
  }
}

function checkTargetedDrill(selected, correct, explanation, btn) {
  const container = document.getElementById('targeted-drill-container');
  const feedbackEl = document.getElementById('targeted-drill-feedback');

  if (container) {
    container.querySelectorAll('.option-btn').forEach(b => {
      b.disabled = true;
      if (b === btn) b.classList.add('selected');
    });
  }

  if (selected === correct) {
    btn.classList.add('correct');
    if (feedbackEl) {
      feedbackEl.className = 'practice-feedback show correct';
      feedbackEl.innerHTML = `<strong>✔ Drill Mastered!</strong> ${escapeHTML(explanation || 'You have strengthened this concept!')}`;
    }
  } else {
    btn.classList.add('incorrect');
    if (feedbackEl) {
      feedbackEl.className = 'practice-feedback show incorrect';
      feedbackEl.innerHTML = `<strong>✖ Keep practicing.</strong> Correct answer: <em>${escapeHTML(correct)}</em>.<br>${escapeHTML(explanation || '')}`;
    }
  }
}

function retestTopic() {
  navigateTo('test');
  initiateTest();
}

// ==========================================================================
// 10. PROGRESS MATRIX & DASHBOARD ANALYTICS (Matching Image 1)
// ==========================================================================

async function loadProgress() {
  try {
    const res = await fetch(`${state.apiBase}/progress`);
    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);

    const data = await res.json();
    renderProgress(data);
  } catch (err) {
    console.error('Error fetching progress:', err);
  }
}

function renderProgress(data) {
  // Update Analytics Matrix
  const progTotal = document.getElementById('prog-total-attempts');
  const progAcc = document.getElementById('prog-overall-acc');
  const progMastered = document.getElementById('prog-mastered-count');
  const progWeak = document.getElementById('prog-weak-count');

  if (progTotal) progTotal.textContent = data.total_attempts || 0;
  if (progAcc) progAcc.textContent = `${Math.round(data.average_score || 0)}%`;
  if (progMastered) progMastered.textContent = (data.strong_concepts || []).length;
  if (progWeak) progWeak.textContent = (data.weak_concepts || []).length;

  // Update Dashboard Cards
  const dashTopics = document.getElementById('dash-topics-count');
  const dashTests = document.getElementById('dash-tests-count');
  const dashAvg = document.getElementById('dash-avg-score');

  if (dashTopics) dashTopics.textContent = data.topics_studied || 0;
  if (dashTests) dashTests.textContent = data.total_attempts || 0;
  if (dashAvg) dashAvg.textContent = data.total_attempts > 0 ? `${Math.round(data.average_score || 0)}%` : '--';

  // Handle Realistic Empty State for Study Activity (Matching Image 1)
  const activityContainer = document.getElementById('activity-bars-container');
  const activityEmptyState = document.getElementById('activity-empty-state');
  const activityMetric = document.getElementById('dash-activity-metric');

  if (data.total_attempts === 0) {
    if (activityEmptyState) activityEmptyState.classList.remove('hidden');
    if (activityMetric) activityMetric.textContent = '0 hrs';
  } else {
    if (activityEmptyState) activityEmptyState.classList.add('hidden');
    if (activityMetric) activityMetric.textContent = `${(data.total_attempts * 1.5).toFixed(1)} hrs`;
  }

  // Concept Matrix
  const matrixContainer = document.getElementById('progress-concept-matrix');
  if (matrixContainer) {
    matrixContainer.innerHTML = '';
    const allConcepts = data.concept_mastery || [];

    if (allConcepts.length === 0) {
      matrixContainer.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem; padding: 1rem 0;">No concepts tested yet. Complete an assessment to start tracking mastery!</p>`;
    } else {
      allConcepts.forEach(c => {
        const row = document.createElement('div');
        row.className = 'concept-row';
        const isMastered = c.accuracy >= 75;
        row.innerHTML = `
          <div>
            <strong>${escapeHTML(c.concept)}</strong>
            <span style="font-size: 0.75rem; color: var(--text-dim); margin-left: 0.5rem;">(${escapeHTML(c.topic)})</span>
            <div style="font-size: 0.78rem; color: var(--text-muted);">${c.correct}/${c.tested} correct (${Math.round(c.accuracy)}%)</div>
          </div>
          <span class="concept-status-badge ${isMastered ? 'status-mastered' : 'status-weak'}">
            ${isMastered ? 'Mastered 🌟' : 'Needs Practice ⚠️'}
          </span>
        `;
        matrixContainer.appendChild(row);
      });
    }
  }

  // History List
  const historyContainer = document.getElementById('progress-history-list');
  if (historyContainer) {
    historyContainer.innerHTML = '';
    const attempts = data.recent_attempts || [];

    if (attempts.length === 0) {
      historyContainer.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem; padding: 1rem 0;">No assessment history recorded yet.</p>`;
    } else {
      attempts.forEach(att => {
        const row = document.createElement('div');
        row.className = 'concept-row';
        const pct = Math.round(att.score_percentage || 0);
        row.innerHTML = `
          <div>
            <strong>${escapeHTML(att.topic)}</strong> (${escapeHTML(att.difficulty)})
            <div style="font-size: 0.78rem; color: var(--text-dim);">${new Date(att.created_at).toLocaleString()}</div>
          </div>
          <div>
            <strong style="color: ${pct >= 75 ? 'var(--success-text)' : 'var(--warning-text)'};">${pct}%</strong>
            <span style="font-size: 0.78rem; color: var(--text-dim);">(${att.correct_count}/${att.total_questions})</span>
          </div>
        `;
        historyContainer.appendChild(row);
      });
    }
  }
}

// ==========================================================================
// 11. CALENDAR STRIP COMPONENT (Matching Reference Image 1)
// ==========================================================================

function renderCalendarStrip() {
  const container = document.getElementById('calendar-days-strip');
  const monthNameEl = document.getElementById('cal-month-name');
  if (!container) return;

  const now = new Date();
  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  if (monthNameEl) {
    monthNameEl.textContent = `${monthNames[now.getMonth()]}, ${now.getFullYear()}`;
  }

  container.innerHTML = '';
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Generate 7 days centered on today
  for (let offset = -3; offset <= 3; offset++) {
    const d = new Date();
    d.setDate(now.getDate() + offset);

    const isToday = (offset === 0);
    const dayPill = document.createElement('div');
    dayPill.className = `calendar-day-pill ${isToday ? 'active' : ''}`;
    dayPill.innerHTML = `
      <span class="cal-day-name">${dayNames[d.getDay()]}</span>
      <span class="cal-day-num">${String(d.getDate()).padStart(2, '0')}</span>
    `;

    dayPill.onclick = () => {
      document.querySelectorAll('.calendar-day-pill').forEach(p => p.classList.remove('active'));
      dayPill.classList.add('active');
    };

    container.appendChild(dayPill);
  }
}

// ==========================================================================
// 12. UTILITIES & ESCAPING
// ==========================================================================

function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeQuotes(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  renderCalendarStrip();
  navigateTo('dashboard');
  loadProgress();
});

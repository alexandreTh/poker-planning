const allowedVotes = ['0', '1', '2', '3', '5', '8', '13', '21', '?'];

const firstNameInput = document.getElementById('firstName');
const registerBtn = document.getElementById('registerBtn');
const voteButtonsContainer = document.getElementById('voteButtons');
const revealBtn = document.getElementById('revealBtn');
const resetBtn = document.getElementById('resetBtn');
const statusElement = document.getElementById('status');
const resultsElement = document.getElementById('results');
const averageElement = document.getElementById('average');
const participantsElement = document.getElementById('participants');

function getFirstName() {
  return firstNameInput.value.trim();
}

function setStatus(message) {
  statusElement.textContent = message;
}

function sortVotes(a, b) {
  if (a === '?') {
    return 1;
  }
  if (b === '?') {
    return -1;
  }
  return Number(a) - Number(b);
}

async function fetchState() {
  const response = await fetch('/api/state');
  return response.json();
}

function renderState(state) {
  const participants = state.participantsStatus || [];
  const votesSubmitted = state.votesSubmitted || 0;
  const totalParticipants = state.totalParticipants || 0;

  if (participants.length === 0) {
    participantsElement.innerHTML = '<p>Aucun participant pour le moment.</p>';
  } else {
    const items = participants
      .map((participant) => `<li>${participant.firstName}: ${participant.hasVoted ? 'a vote' : 'pas encore vote'}</li>`)
      .join('');
    participantsElement.innerHTML = `<ul>${items}</ul>`;
  }

  if (!state.revealed) {
    setStatus(`Vote en cours. ${votesSubmitted}/${totalParticipants} participant(s) ont vote.`);
    resultsElement.innerHTML = '<p>Les votes sont caches jusqu\'au reveal.</p>';
    averageElement.textContent = '';
    return;
  }

  setStatus(`Resultats reveles automatiquement. ${votesSubmitted}/${totalParticipants} participant(s) ont vote.`);
  const entries = Object.entries(state.distribution || {}).sort(([voteA], [voteB]) => sortVotes(voteA, voteB));
  if (entries.length === 0) {
    resultsElement.innerHTML = '<p>Aucun vote a afficher.</p>';
  } else {
    const cards = entries
      .map(([vote, count]) => {
        const percent = votesSubmitted > 0 ? Math.round((count / votesSubmitted) * 100) : 0;
        return `
          <article class="result-card">
            <p class="result-vote">${vote}</p>
            <p class="result-count">${count} vote(s)</p>
            <div class="result-bar">
              <span style="width: ${percent}%"></span>
            </div>
            <p class="result-percent">${percent}%</p>
          </article>
        `;
      })
      .join('');
    resultsElement.innerHTML = `<div class="results-grid">${cards}</div>`;
  }
  averageElement.textContent =
    state.average === null || state.average === undefined
      ? 'Moyenne: non calculable (seulement des votes "?").'
      : `Moyenne: ${state.average}`;
}

async function refreshState() {
  try {
    const state = await fetchState();
    renderState(state);
  } catch (_error) {
    setStatus('Erreur reseau.');
  }
}

async function submitVote(vote) {
  const firstName = getFirstName();
  if (firstName.length < 2) {
    alert('Entrez votre prenom (2 caracteres min).');
    return;
  }

  const response = await fetch('/api/vote', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ firstName, vote })
  });

  const payload = await response.json();
  if (!response.ok) {
    alert(payload.error || 'Erreur pendant le vote.');
    return;
  }

  await refreshState();
}

async function registerParticipant() {
  const firstName = getFirstName();
  if (firstName.length < 2) {
    alert('Entrez votre prenom (2 caracteres min).');
    return;
  }

  const response = await fetch('/api/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ firstName })
  });

  const payload = await response.json();
  if (!response.ok) {
    alert(payload.error || 'Erreur pendant l\'inscription.');
    return;
  }

  await refreshState();
}

async function revealVotes() {
  await fetch('/api/reveal', { method: 'POST' });
  await refreshState();
}

async function resetVotes() {
  await fetch('/api/reset', { method: 'POST' });
  await refreshState();
}

for (const vote of allowedVotes) {
  const button = document.createElement('button');
  button.textContent = vote;
  button.addEventListener('click', () => submitVote(vote));
  voteButtonsContainer.appendChild(button);
}

revealBtn.addEventListener('click', revealVotes);
resetBtn.addEventListener('click', resetVotes);
registerBtn.addEventListener('click', registerParticipant);

refreshState();
setInterval(refreshState, 3000);

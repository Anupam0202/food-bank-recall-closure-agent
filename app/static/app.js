const csrf = () => document.querySelector('meta[name="csrf-token"]')?.content || '';
const toast = (message, kind = 'ok') => {
  const node = document.getElementById('toast');
  if (!node) return;
  node.textContent = message; node.dataset.kind = kind; node.hidden = false;
  setTimeout(() => { node.hidden = true; }, 4000);
};
const post = async (url, body = {}) => {
  const response = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf()},
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
};

document.addEventListener('click', async (event) => {
  const run = event.target.closest('#run-demo');
  const reset = event.target.closest('#reset-demo');
  const ack = event.target.closest('.ack-task');
  const resolve = event.target.closest('.resolve-match');
  try {
    if (run) {
      run.disabled = true; run.textContent = 'Running response…';
      const data = await post('/api/demo/run-golden-path');
      window.location.href = `/incidents/${data.incident.id}`;
    } else if (reset) {
      reset.disabled = true;
      await post('/api/demo/reset');
      window.location.reload();
    } else if (ack) {
      await post(`/api/tasks/${ack.dataset.taskId}/acknowledge`, {actor: 'Demo partner lead', note: 'Affected stock isolated and counted.'});
      window.location.reload();
    } else if (resolve) {
      await post(`/api/matches/${resolve.dataset.matchId}/resolve`, {resolution: 'Inspected by partner: no recalled lot code present'});
      toast('Human review recorded');
      window.location.reload();
    }
  } catch (error) {
    toast(error.message, 'error');
    if (run) { run.disabled = false; run.textContent = 'Run seeded demonstration'; }
    if (reset) reset.disabled = false;
  }
});


document.addEventListener('submit', async (event) => {
  if (event.target.id !== 'notice-upload') return;
  event.preventDefault();
  const form = event.target;
  const button = form.querySelector('button');
  button.disabled = true; button.textContent = 'Extracting notice…';
  try {
    const response = await fetch('/api/recalls/ingest', {method: 'POST', headers: {'X-CSRF-Token': csrf()}, body: new FormData(form)});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || 'Upload failed');
    window.location.href = `/incidents/${data.incident.id}`;
  } catch (error) {
    toast(error.message, 'error'); button.disabled = false; button.textContent = 'Ingest notice';
  }
});


document.addEventListener('submit', async (event) => {
  const form = event.target.closest('.evidence-form');
  if (!form) return;
  event.preventDefault();
  const button = form.querySelector('button');
  button.disabled = true; button.textContent = 'Uploading…';
  try {
    const response = await fetch(`/api/tasks/${form.dataset.taskId}/evidence`, {method: 'POST', headers: {'X-CSRF-Token': csrf()}, body: new FormData(form)});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || 'Evidence upload failed');
    toast('Private completion evidence recorded');
    window.location.reload();
  } catch (error) {
    toast(error.message, 'error'); button.disabled = false; button.textContent = 'Upload evidence';
  }
});

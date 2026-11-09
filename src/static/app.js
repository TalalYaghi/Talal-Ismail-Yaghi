const $ = (selector) => document.querySelector(selector);
let tasks = [];
let toastTimer;
const dialog = $('#task-dialog');
const form = $('#task-form');

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json' } });
  const payload = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(payload?.error || 'Something went wrong. Please try again.');
  return payload;
}

function notify(message) {
  $('#toast').textContent = message;
  $('#toast').classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('#toast').classList.remove('visible'), 3500);
}

function node(tag, className, text) {
  const element = document.createElement(tag);
  element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function card(task) {
  const element = node('button', `task-card ${task.status === 'done' ? 'done-card' : ''}`);
  element.type = 'button';
  element.setAttribute('aria-label', `Edit ${task.title}`);
  const top = node('div', 'card-top');
  top.append(node('span', 'course', task.course || 'Personal'), node('span', `priority ${task.priority}`, `${task.priority[0].toUpperCase()}${task.priority.slice(1)}`));
  const bottom = node('div', 'card-bottom');
  let dueText = 'No due date';
  let overdue = false;
  if (task.due_date) {
    const due = new Date(`${task.due_date}T00:00:00`);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    overdue = due < today && task.status !== 'done';
    dueText = due.toLocaleDateString('en', { month: 'short', day: 'numeric' });
    if (due.getFullYear() !== today.getFullYear()) dueText += `, ${due.getFullYear()}`;
    if (overdue) dueText += ' · Overdue';
  }
  bottom.append(node('span', `due ${overdue ? 'overdue' : ''}`, `▦  ${dueText}`), node('span', 'card-avatar', 'TY'));
  element.append(top, node('h4', '', task.title));
  if (task.notes) element.append(node('p', '', task.notes));
  element.append(bottom);
  element.addEventListener('click', () => openTask(task));
  return element;
}

function render() {
  const query = $('#search').value.trim().toLowerCase();
  const priority = $('#priority-filter').value;
  const visible = tasks.filter(task => (!priority || task.priority === priority) && `${task.title} ${task.course} ${task.notes}`.toLowerCase().includes(query));
  $('#total-count').textContent = tasks.length;
  $('#progress-count').textContent = tasks.filter(task => task.status === 'progress').length;
  $('#done-count').textContent = tasks.filter(task => task.status === 'done').length;
  $('#result-count').textContent = query || priority ? `Showing ${visible.length} of ${tasks.length} tasks` : 'Your next steps, all in one place.';
  const countIds = { todo: '#todo-count', progress: '#progress-column-count', done: '#done-column-count' };
  for (const status of ['todo', 'progress', 'done']) {
    const list = $(`#${status}-list`);
    const matches = visible.filter(task => task.status === status);
    $(countIds[status]).textContent = matches.length;
    list.replaceChildren(...matches.map(card));
    if (!matches.length) list.append(node('div', 'empty-state', query || priority ? 'No matching tasks.' : { todo: 'A fresh start. Add your first task.', progress: 'Ready when you are. Start something.', done: 'Your next small win belongs here.' }[status]));
  }
}

async function load() {
  tasks = await api('/api/tasks');
  render();
}

function openTask(task = null, status = 'todo') {
  form.reset();
  form.elements.id.value = task?.id || '';
  for (const key of ['title', 'course', 'notes', 'due_date', 'priority', 'status']) {
    form.elements[key].value = task?.[key] ?? ({ priority: 'medium', status }[key] || '');
  }
  $('#dialog-title').textContent = task ? 'Edit task' : 'New task';
  $('#save-task').textContent = task ? 'Save changes' : 'Create task';
  $('#delete-task').hidden = !task;
  $('#form-error').textContent = '';
  dialog.showModal();
  form.elements.title.focus();
}

$('#new-task').addEventListener('click', () => openTask());
document.querySelectorAll('.add-task').forEach(button => button.addEventListener('click', () => openTask(null, button.dataset.status)));
$('#close-dialog').addEventListener('click', () => dialog.close());
$('#cancel-dialog').addEventListener('click', () => dialog.close());
$('#search').addEventListener('input', render);
$('#priority-filter').addEventListener('change', render);

form.addEventListener('submit', async event => {
  event.preventDefault();
  const id = form.elements.id.value;
  const values = Object.fromEntries(new FormData(form));
  delete values.id;
  $('#save-task').disabled = true;
  $('#form-error').textContent = '';
  try {
    const saved = await api(id ? `/api/tasks/${id}` : '/api/tasks', { method: id ? 'PATCH' : 'POST', body: JSON.stringify(values) });
    tasks = id ? tasks.map(task => task.id === saved.id ? saved : task) : [saved, ...tasks];
    render();
    dialog.close();
    notify(id ? 'Task updated. Keep moving forward.' : 'Task created. One step closer.');
  } catch (error) { $('#form-error').textContent = error.message; }
  finally { $('#save-task').disabled = false; }
});

$('#delete-task').addEventListener('click', async () => {
  if (!confirm('Delete this task? This cannot be undone.')) return;
  const id = Number(form.elements.id.value);
  $('#delete-task').disabled = true;
  try {
    await api(`/api/tasks/${id}`, { method: 'DELETE' });
    tasks = tasks.filter(task => task.id !== id);
    render();
    dialog.close();
    notify('Task deleted.');
  } catch (error) { $('#form-error').textContent = error.message; }
  finally { $('#delete-task').disabled = false; }
});

load().catch(error => {
  notify(`Could not load tasks: ${error.message}`);
  $('#result-count').textContent = 'Unable to load tasks. Check the connection and refresh.';
});

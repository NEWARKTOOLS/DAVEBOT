const state = {
  customers: [],
  jobs: [],
  quotes: [],
  inventory: [],
};

const api = async (path, options = {}) => {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || 'Request failed');
  }
  return response.json();
};

const renderList = (containerId, items, formatter) => {
  const container = document.getElementById(containerId);
  container.innerHTML = '';
  if (items.length === 0) {
    container.innerHTML = '<div class="table-item">No records yet.</div>';
    return;
  }
  items.forEach((item) => {
    const div = document.createElement('div');
    div.className = 'table-item';
    div.innerHTML = formatter(item);
    container.appendChild(div);
  });
};

const updateMetrics = () => {
  document.getElementById('metric-jobs').textContent = state.jobs.length;
  document.getElementById('metric-quotes').textContent = state.quotes.length;
  document.getElementById('metric-inventory').textContent = state.inventory.length;
};

const loadData = async () => {
  try {
    state.customers = await api('/customers');
    state.jobs = await api('/jobs');
    state.quotes = await api('/quotes');
    state.inventory = await api('/inventory');
  } catch (error) {
    console.error(error);
  }

  updateMetrics();

  renderList('job-table', state.jobs, (job) => `
    <strong>${job.job_type.replace('_', ' ')}</strong>
    <div>Status: ${job.status}</div>
    <div>Job ID: ${job.id}</div>
    <div>Customer: ${job.customer_id}</div>
  `);

  renderList('quote-table', state.quotes, (quote) => `
    <strong>Quote ${quote.id.slice(0, 8)}</strong>
    <div>Customer: ${quote.customer_id}</div>
    <div>Job: ${quote.job_id || 'N/A'}</div>
    <div>Subtotal: £${quote.totals?.subtotal?.toFixed?.(2) ?? '0.00'}</div>
  `);

  renderList('inventory-table', state.inventory, (item) => `
    <strong>${item.description}</strong>
    <div>Category: ${item.category}</div>
    <div>Stock: ${item.stock_on_hand} ${item.unit}</div>
    <div>Reorder: ${item.reorder_point}</div>
  `);
};

const handleForm = (formId, submitFn, statusId) => {
  const form = document.getElementById(formId);
  const status = document.getElementById(statusId);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    status.textContent = 'Saving...';
    try {
      await submitFn(new FormData(form));
      status.textContent = 'Saved.';
      form.reset();
      await loadData();
    } catch (error) {
      status.textContent = error.message;
    }
  });
};

handleForm('job-form', async (data) => {
  const payload = Object.fromEntries(data.entries());
  await api('/jobs', { method: 'POST', body: JSON.stringify(payload) });
}, 'job-status');

handleForm('quote-form', async (data) => {
  const payload = Object.fromEntries(data.entries());
  const lineItem = {
    description: payload.line_description || 'Labor',
    unit_cost: Number(payload.line_unit_cost || 0),
    quantity: Number(payload.line_quantity || 1),
  };
  const body = {
    customer_id: payload.customer_id,
    job_id: payload.job_id || null,
    line_items: [lineItem],
  };
  await api('/quotes', { method: 'POST', body: JSON.stringify(body) });
}, 'quote-status');

handleForm('inventory-form', async (data) => {
  const payload = Object.fromEntries(data.entries());
  payload.stock_on_hand = Number(payload.stock_on_hand || 0);
  payload.reorder_point = Number(payload.reorder_point || 0);
  await api('/inventory', { method: 'POST', body: JSON.stringify(payload) });
}, 'inventory-status');

const calculatorHandler = (formId, endpoint, resultId) => {
  const form = document.getElementById(formId);
  const result = document.getElementById(resultId);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(form).entries());
    Object.keys(payload).forEach((key) => {
      payload[key] = Number(payload[key]);
    });
    result.textContent = 'Calculating...';
    try {
      const data = await api(endpoint, { method: 'POST', body: JSON.stringify(payload) });
      result.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
      result.textContent = error.message;
    }
  });
};

calculatorHandler('tooling-calculator', '/calculators/tooling', 'tooling-result');
calculatorHandler('moulding-calculator', '/calculators/moulding', 'moulding-result');

const assistantForm = document.getElementById('assistant-form');
const assistantChat = document.getElementById('assistant-chat');
const cannedAnswers = [
  'For tooling quotes, remember to factor in engineering hours, machining hours, and tryout rounds.',
  'P20 is a good pre-hardened steel for general mould work; H13 is better for high wear.',
  'Cycle time improvements usually come from better cooling and balanced runner design.',
  'Consider adding 5-10% scrap allowance for new materials or complex parts.',
];

assistantForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const input = assistantForm.querySelector('input[name="question"]');
  const question = input.value.trim();
  if (!question) return;

  const userMessage = document.createElement('div');
  userMessage.className = 'chat-message user';
  userMessage.textContent = question;
  assistantChat.appendChild(userMessage);

  const botMessage = document.createElement('div');
  botMessage.className = 'chat-message bot';
  botMessage.textContent = cannedAnswers[Math.floor(Math.random() * cannedAnswers.length)];
  assistantChat.appendChild(botMessage);

  assistantChat.scrollTop = assistantChat.scrollHeight;
  input.value = '';
});

loadData();

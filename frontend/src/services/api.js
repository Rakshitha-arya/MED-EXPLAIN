const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

async function handleResponse(response) {
  const contentType = response.headers.get('content-type');
  let data = {};
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    const text = await response.text();
    data = { message: text };
  }

  if (!response.ok) {
    const errorMessage =
      data.error || data.message || `Server returned status ${response.status}`;
    throw new Error(errorMessage);
  }

  return data;
}

export async function uploadReport(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/reports/upload`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse(response);
}

export async function analyzeReport(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/reports/analyze`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse(response);
}

export async function getReportExplanation(reportId, question = '') {
  const response = await fetch(
    `${API_BASE_URL}/api/reports/${encodeURIComponent(reportId)}/explain`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question:
          question || 'Can you explain my medical report results in simple terms?',
      }),
    }
  );

  return handleResponse(response);
}

export async function sendReportChat(reportId, question) {
  const response = await fetch(
    `${API_BASE_URL}/api/reports/${encodeURIComponent(reportId)}/chat`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    }
  );

  return handleResponse(response);
}

export async function getReports() {
  const response = await fetch(`${API_BASE_URL}/api/reports`, {
    method: 'GET',
  });

  return handleResponse(response);
}

export async function compareReports(reportIds) {
  const response = await fetch(`${API_BASE_URL}/api/reports/compare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ report_ids: reportIds }),
  });

  return handleResponse(response);
}

export async function getTrends(parameterName) {
  const response = await fetch(
    `${API_BASE_URL}/api/reports/trends?parameter=${encodeURIComponent(parameterName)}`,
    {
      method: 'GET',
    }
  );

  return handleResponse(response);
}

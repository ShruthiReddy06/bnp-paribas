import { apiRequest } from './client.js'

export function getJobs(token) {
  return apiRequest('/candidate/jobs', { token })
}

export function createJob(token, job) {
  return apiRequest('/admin/jobs', { method: 'POST', body: job, token })
}

export function getApplications(token) {
  return apiRequest('/candidate/applications', { token })
}

export function getMyApplications(token) {
  return apiRequest('/candidate/my-applications', { token })
}

export function getCandidateTests(token) {
  return apiRequest('/candidate/tests', { token })
}

export function startCandidateTest(token, testId) {
  return apiRequest(`/candidate/tests/${testId}/start`, { method: 'POST', token })
}

export function submitCandidateTest(token, testId, answers) {
  return apiRequest(`/candidate/tests/${testId}/submit`, { method: 'POST', body: { answers }, token })
}

export function applyForJob(token, jobId, resume) {
  const body = new FormData()
  body.append('resume', resume)
  return apiRequest(`/candidate/jobs/${jobId}/apply`, { method: 'POST', body, token })
}
import { apiRequest } from './client.js'

// GET /admin/candidates -> [{ id, name, jd, status, score, decision }]
export function getCandidates(token) {
  return apiRequest('/admin/candidates', { token })
}

export function getUsers(token) {
  return apiRequest('/admin/users', { token })
}

export function getApplications(token) {
  return apiRequest('/admin/applications', { token })
}

export function assignCandidateTest(token, applicationId) {
  return apiRequest(`/admin/applications/${applicationId}/assign-test`, { method: 'POST', token })
}

export function assignInterviewer(token, applicationId, interviewerUsername) {
  return apiRequest('/admin/interviews/assign', {
    method: 'POST', token,
    body: { application_id: applicationId, interviewer_username: interviewerUsername }
  })
}

export function getAdminJobs(token) {
  return apiRequest('/admin/jobs', { token })
}

export function deleteJob(token, jobId) {
  return apiRequest(`/admin/jobs/${jobId}`, { method: 'DELETE', token })
}

export function deleteUser(token, username) {
  return apiRequest(`/admin/users/${encodeURIComponent(username)}`, { method: 'DELETE', token })
}

export function getShortlistThreshold(token) {
  return apiRequest('/admin/settings/threshold', { token })
}

export function updateShortlistThreshold(token, threshold) {
  return apiRequest('/admin/settings/threshold', { method: 'PUT', body: { threshold }, token })
}

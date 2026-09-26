import { apiRequest } from './client.js'

// GET /interviewer/candidates -> [{ id, name, jd, status, score, decision }]
export function getAssignedCandidates(token) {
  return apiRequest('/interviewer/candidates', { token })
}

// POST /interviewer/decision -> { ok, candidate_id, decision }
export function submitDecision(token, candidateId, decision) {
  return apiRequest('/interviewer/decision', {
    method: 'POST',
    token,
    body: { interview_id: candidateId, decision, feedback: '' }
  })
}

export function scheduleInterview(token, applicationId, scheduledAt) {
  return apiRequest('/interviewer/schedule', {
    method: 'POST', token, body: { application_id: applicationId, scheduled_at: scheduledAt }
  })
}

export function saveInterviewDecision(token, interviewId, decision, feedback) {
  return apiRequest('/interviewer/decision', {
    method: 'POST', token, body: { interview_id: interviewId, decision, feedback }
  })
}

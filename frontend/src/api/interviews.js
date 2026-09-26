import { apiRequest } from './client.js'

export function getCandidateInterviews(token) {
  return apiRequest('/candidate/interviews', { token })
}

export function confirmInterview(token, interviewId) {
  return apiRequest(`/candidate/interviews/${interviewId}/confirm`, { method: 'POST', token })
}
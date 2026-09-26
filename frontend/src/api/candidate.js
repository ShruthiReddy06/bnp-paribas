import { apiRequest } from './client.js'

// GET /candidate/status -> { status, jd, interviewer_name, interview_date }
export function getStatus(token) {
  return apiRequest('/candidate/status', { token })
}

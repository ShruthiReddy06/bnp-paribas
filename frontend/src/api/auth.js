import { apiRequest } from './client.js'

// POST /login -> { token, role, username }
export function login(username, password, accessScope = 'standard') {
  return apiRequest('/login', {
    method: 'POST',
    body: { username, password, access_scope: accessScope }
  })
}

export function register(username, password, role) {
  return apiRequest('/register', {
    method: 'POST',
    body: { username, password, role }
  })
}

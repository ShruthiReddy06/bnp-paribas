import { createContext, useState } from 'react'
import { login as loginRequest, register as registerRequest } from '../api/auth.js'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(null) // { token, role, username }

  async function login(username, password) {
    const data = await loginRequest(username, password)
    setAuth(data)
    return data
  }

  async function register(username, password, role) {
    const data = await registerRequest(username, password, role)
    setAuth(data)
    return data
  }

  function logout() {
    setAuth(null)
  }

  return (
    <AuthContext.Provider value={{ auth, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

import { createContext, useState } from 'react'
import { login as loginRequest, register as registerRequest } from '../api/auth.js'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem('smarthire-auth') || 'null')
    } catch {
      return null
    }
  })

  async function login(username, password, accessScope) {
    const data = await loginRequest(username, password, accessScope)
    setAuth(data)
    sessionStorage.setItem('smarthire-auth', JSON.stringify(data))
    return data
  }

  async function register(username, password, role) {
    const data = await registerRequest(username, password, role)
    setAuth(data)
    sessionStorage.setItem('smarthire-auth', JSON.stringify(data))
    return data
  }

  function logout() {
    setAuth(null)
    sessionStorage.removeItem('smarthire-auth')
  }

  return (
    <AuthContext.Provider value={{ auth, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

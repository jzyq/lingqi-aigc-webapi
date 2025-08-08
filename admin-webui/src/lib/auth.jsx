import { createContext } from "react"

const TOKEN_KEY = "auth_token"

export const AuthProvider = createContext([null, () => { }])

export function getLocalAuthToken() {
    return localStorage.getItem(TOKEN_KEY)
}

export function setLocalAuthToken(tk) {
    localStorage.setItem(TOKEN_KEY, tk)
}

export default AuthProvider
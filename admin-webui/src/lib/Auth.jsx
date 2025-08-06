import { useState } from "react";

const key = 'auth_token';
let notifier = null;

export default function useAuthToken() {
    const [_, setToken] = useState(null)
    
    if (notifier === null) {
        notifier = setToken
    }

    const setter = token => {
        localStorage.setItem(key, token)
        notifier(token)
    }

    const clear = () => {
        localStorage.removeItem(key)
        notifier(null)
    }

    const token = localStorage.getItem(key);
    return [token, setter, clear]
}
export const NoAuthError = 'no authorization'

export async function get(url, authToken) {
    if (authToken === null) {
        throw NoAuthError
    }

    const headers = {
        'content-type': 'application/json',
        'authorization': `bearer ${authToken}`
    }

    const resp = await fetch(url, {
        method: 'GET',
        headers: headers,
    })

    if (resp.status === 401) {
        throw NoAuthError
    }
    if (resp.status === 200) {
        return await resp.json()
    }

    throw resp.statusText
}

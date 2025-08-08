import styled from "@emotion/styled"
import { useState, useContext } from "react"
import AuthProvider from "../lib/Auth"

const StyledContainer = styled.div`
    display: flex;
    width: 100vw;
    height: 100vh;
    align-items: center;
    justify-content: center;
`

const InputBox = styled.div`
    display: flex;
    flex-direction: column;
    gap: 4px;
`

const InputItem = styled.section`
    display: flex;
`

const Label = styled.label`
    font-size: 14px;
    width: 6em;
`

const Input = styled.input`
    font-size: 14px;
    width: 10em;
`

const Button = styled.button`
    font-size: 14px;
    width: stretch;
    padding: auto;
`

const LoginURL = '/aigc/admin/api/auth/login'

export default function Login() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const [tk, setToken] = useContext(AuthProvider)

    const login = () => {
        fetch(LoginURL, {
            method: "POST",
            headers: {
                'content-type': "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        }).then(resp => {
            if (resp.status !== 200) {
                throw `server error when login: ${resp.statusText}`
            }
            return resp.json()
        }).then(data => {
            if (data.code !== 0) {
                throw `login failed: ${data.msg}`
            }
            setToken(data.data.token)
        }).catch(alert)
    }


    return <StyledContainer>
        <InputBox>
            <h1 style={{ margin: '0px auto 8px' }}>AIGC Admin</h1>
            <InputItem>
                <Label>Username</Label>
                <Input type="text" value={username} onChange={e => setUsername(e.target.value)} />
            </InputItem>
            <InputItem>
                <Label>Password</Label>
                <Input type="password" value={password} onChange={e => setPassword(e.target.value)} />
            </InputItem>
            <InputItem style={{ marginTop: '8px' }}>
                <Button onClick={login}>Login in</Button>
            </InputItem>
        </InputBox>

    </StyledContainer>
}
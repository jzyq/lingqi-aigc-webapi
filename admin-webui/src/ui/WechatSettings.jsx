import { useState, useEffect, useContext } from "react"
import { NoAuthError, get } from "../lib/http"
import AuthProvider from "../lib/Auth"
import Button from "@mui/material/Button"
import TextField from "@mui/material/TextField"
import Container from "@mui/material/Container"
import Stack from "@mui/material/Stack"
import Typography from "@mui/material/Typography"

const secretsURL = "/aigc/admin/api/sysconf/wechat/secrets"
const loginCallbackURL = "/aigc/admin/api/sysconf/wechat/login_callback"
const paymentCallbackURL = "/aigc/admin/api/sysconf/wechat/payment_callback"
const paymentExpiresURL = "/aigc/admin/api/sysconf/wechat/payment_expires"

function StyledTextInput(props) {
    return <TextField
        variant="outlined"
        fullWidth
        margin="dense"
        size="small"
        {...props}
    >
        {props.children}
    </TextField>
}

function Title(props) {
    return <Typography variant="subtitle1" gutterBottom>
        {props.children}
    </Typography>
}

function InputGroup(props) {
    return <Stack
        spacing={2}
        {...props}
        height={'100%'}
    >
        {props.children}
    </Stack>
}

function InputHBox(props) {
    return <Stack
        direction="row"
        spacing={2}
        {...props}
        height={'100%'}
    >
        {props.children}
    </Stack>
}

function SecretsPanel() {
    const [token, setToken] = useContext(AuthProvider)

    const [secrets, setSecrets] = useState({
        login_id: "",
        app_id: "",
        app_secret: "",
        mch_id: "",
        mch_cert_serial: "",
        pub_key_id: "",
        api_v3_pwd: "",
        api_client_key: "",
        pub_key: "",
    })
    const [loginCallback, setLoginCallback] = useState("")
    const [payCallback, setPayCallback] = useState("")
    const [payExpires, setPayExpires] = useState(0)

    const fetchData = async () => {
        try {
            // Fetch secrets data
            let data = await get(secretsURL, token);
            if (data.code !== 0) {
                throw `fetch wechat secrets error: ${data.msg}`;
            }
            setSecrets(data.data);

            // Fetch login callback url
            data = await get(loginCallbackURL, token);
            if (data.code !== 0) {
                throw `fetch wechat login callback url error: ${data.msg}`;
            }
            setLoginCallback(data.data.url);

            // Fetch payment callbck url
            data = await get(paymentCallbackURL, token);
            if (data.code !== 0) {
                throw `fetch payment callback url error: ${data.msg}`;
            }
            setPayCallback(data.data.url);

            // Fetch payment expires
            data = await get(paymentExpiresURL, token);
            if (data.code !== 0) {
                throw `fetch payment expires error: ${data.msg}`
            }
            setPayExpires(data.data.seconds)

        } catch (e) {
            if (e === NoAuthError) {
                setToken(null)
                return
            }
            alert(e)
        }
    }

    useEffect(() => {
        fetchData();
    }, [])


    const saveChange = () => {
        const p1 = fetch(secretsURL, {
            method: "POST",
            headers: {
                'content-type': 'application/json',
                'authorization': `bearer ${token}`
            },
            body: JSON.stringify(secrets)
        }).then(resp => {
            if (resp.status !== 200) {
                throw `server error when set wechat secrets: ${resp.statusText}`;
            }
        })

        const p2 = fetch(loginCallbackURL, {
            method: 'POST',
            headers: {
                'content-type': 'application/json',
                'authorization': `bearer ${authToken}`
            },
            body: JSON.stringify({ url: loginCallback })
        }).then(resp => {
            if (resp.status !== 200) {
                throw `server error when set wechat login callback: ${resp.statusText}`
            }
        })

        const p3 = fetch(paymentCallbackURL, {
            method: 'POST',
            headers: {
                'content-type': 'application/json',
                'authorization': `bearer ${authToken}`
            },
            body: JSON.stringify({ url: payCallback })
        }).then(resp => {
            if (resp.status !== 200) {
                throw `server error when set wechat payment callback: ${resp.statusText}`
            }
        })

        const p4 = fetch(paymentExpiresURL, {
            method: 'POST',
            headers: {
                'content-type': 'application/json',
                'authorization': `bearer ${authToken}`
            },
            body: JSON.stringify({ val: payExpires })
        }).then(resp => {
            if (resp.status !== 200) {
                throw `server error when set wechat payment expires: ${resp.statusText}`
            }
        })

        Promise.all([p1, p2, p3, p4])
            .then(() => alert("微信设置已保存"))
            .catch(msg => alert(`保存微信设置失败: ${msg}`))
    }

    return <Stack margin={2} spacing={3} height={'stretch'}>
        <InputGroup>
            <Title>扫码登录设置</Title>
            <InputHBox>
                <StyledTextInput
                    id="ipt_login_app_id"
                    label="登录AppID"
                    value={secrets.login_id}
                    onChange={e => setSecrets({ ...secrets, login_id: e.target.value })} />
                <StyledTextInput
                    id="ipt_login_callback_url"
                    label="登录鉴权回调API"
                    value={loginCallback}
                    onChange={e => setLoginCallback(e.target.value)} />
            </InputHBox>
        </InputGroup>

        <InputGroup>
            <Title>支付设置</Title>
            <InputHBox>
                <StyledTextInput
                    id="ipt_mch_id"
                    label="商户ID"
                    value={secrets.mch_id}
                    onChange={e => setSecrets({ ...secrets, mch_id: e.target.value })} />
                <StyledTextInput
                    id="ipt_mch_cret_serial"
                    label="商户证书序列号"
                    value={secrets.mch_cert_serial}
                    onChange={e => setSecrets({ ...secrets, mch_cert_serial: e.target.value })} />
            </InputHBox>
            <InputHBox>
                <StyledTextInput
                    id="ipt_pay_callback_url"
                    label="支付结果回调"
                    value={payCallback}
                    onChange={e => setPayCallback(e.target.value)} />
                <StyledTextInput
                    id="ipt_pay_expires"
                    label="支付有效期(秒)"
                    type="number"
                    min={0}
                    value={payExpires}
                    onChange={e => setPayExpires(e.target.value)} />
            </InputHBox>
        </InputGroup>

        <InputGroup>
            <Title>API设置</Title>
            <InputHBox>
                <StyledTextInput
                    id="ipt_app_id"
                    label="AppID"
                    value={secrets.app_id}
                    onChange={e => setSecrets({ ...secrets, app_id: e.target.value })} />
                <StyledTextInput
                    id="ipt_app_secret"
                    label="AppSecret"
                    value={secrets.app_secret}
                    onChange={e => setSecrets({ ...secrets, app_secret: e.target.value })} />
            </InputHBox>
        </InputGroup>

        <InputGroup>
            <Title>增强安全设置</Title>
            <InputHBox>
                <StyledTextInput
                    id="ipt_pub_key_id"
                    label="公钥ID"
                    value={secrets.pub_key_id}
                    onChange={e => setSecrets({ ...secrets, pub_key_id: e.target.value })} />
                <StyledTextInput
                    id="ipt_api_v3_pwd"
                    label="APIv3密码"
                    value={secrets.api_v3_pwd}
                    onChange={e => setSecrets({ ...secrets, api_v3_pwd: e.target.value })} />
            </InputHBox>
            <InputHBox>
                <StyledTextInput
                    id="ipt_pub_key"
                    multiline
                    label="公钥"
                    maxRows={6}
                    value={secrets.pub_key}
                    onChange={e => setSecrets({ ...secrets, pub_key: e.target.value })} />
                <StyledTextInput
                    id="ipt_apiclient_key"
                    multiline
                    label="私钥"
                    maxRows={6}
                    value={secrets.api_client_key}
                    onChange={e => setSecrets({ ...secrets, api_client_key: e.target.value })} />
            </InputHBox>
        </InputGroup>

        <InputGroup>
            <InputHBox>
                <Button variant="contained" color="success" onClick={saveChange}>应用</Button>
            </InputHBox>
        </InputGroup>
    </Stack>
}

export default function WechatSettingsPanel() {
    return <Container sx={{ height: 'stretch', overflowY: 'auto' }} maxWidth="xl">
        <SecretsPanel />
    </Container>
}
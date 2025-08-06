import styled from "@emotion/styled"
import { useState, useEffect, useContext } from "react"
import { NoAuthError, get } from "../lib/http"
import Router from "../lib/Router"
import useAuthToken from "../lib/Auth"

const Gap = {
    xm: '4px',
    sm: '6px',
    mid: '12px',
    lg: '16px',
    xl: '24px'
}

const StyledContainer = styled.div`
    margin: 12px;
    display: flex;
    justify-content: start;
`

const Box = styled.div`
    margin: ${props => props.gap.mid};
    margin-bottom: ${props => props.gap.xl};
`

const Title = styled.h4`
    margin: 0;
    margin-bottom: ${props => props.gap.sm};
`

const Label = styled.label`
    display: inline-block;
    font-size: 14px;
    min-width: 128px;
`

const StyledInput = styled.input`
    width: 512px;
    font-size: 14px;
`

const StyledTextarea = styled.textarea`
    resize: none;
    width: 640px;
    height: 64px;
`

const StyledButton = styled.button`
    background-color: ${props => props.theme.success};
    border: none;
    font-size: 14px;
    padding: 4px 12px;
    border-radius: 4px;

    :hover {
        background-color: ${props => props.theme.successLighten};
    }

    :active {
        border: 1px solid;
    }
`

const secretsURL = "/aigc/admin/api/sysconf/wechat/secrets"
const loginCallbackURL = "/aigc/admin/api/sysconf/wechat/login_callback"
const paymentCallbackURL = "/aigc/admin/api/sysconf/wechat/payment_callback"
const paymentExpiresURL = "/aigc/admin/api/sysconf/wechat/payment_expires"


function SecretsPanel() {
    const [_, navigateTo] = useContext(Router)
    const [authToken, setAuthToken, clearAuthToken] = useAuthToken()

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
        if (authToken === null) {
            navigateTo("/login")
            return
        }

        try {
            // Fetch secrets data
            let data = await get(secretsURL, authToken);
            if (data.code !== 0) {
                throw `fetch wechat secrets error: ${data.msg}`;
            }
            setSecrets(data.data);

            // Fetch login callback url
            data = await get(loginCallbackURL, authToken);
            if (data.code !== 0) {
                throw `fetch wechat login callback url error: ${data.msg}`;
            }
            setLoginCallback(data.data.url);

            // Fetch payment callbck url
            data = await get(paymentCallbackURL, authToken);
            if (data.code !== 0) {
                throw `fetch payment callback url error: ${data.msg}`;
            }
            setPayCallback(data.data.url);

            // Fetch payment expires
            data = await get(paymentExpiresURL, authToken);
            if (data.code !== 0) {
                throw `fetch payment expires error: ${data.msg}`
            }
            setPayExpires(data.data.seconds)

        } catch (e) {
            if (e === NoAuthError) {
                clearAuthToken()
                navigateTo("/login")
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
                'authorization': `bearer ${authToken}`
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

    return <div>
        <Box gap={Gap}>
            <Title gap={Gap}>扫码登录设置</Title>
            <div>
                <Label>登录AppId</Label>
                <StyledInput type="text" value={secrets.login_id}
                    onChange={e => setSecrets({ ...secrets, login_id: e.target.value })} />
            </div>

            <div>
                <Label>登录鉴权回调API</Label>
                <StyledInput type="text" value={loginCallback}
                    onChange={e => setLoginCallback(e.target.value)} />
            </div>
        </Box>

        <Box gap={Gap}>
            <Title gap={Gap}>支付设置</Title>
            <div>
                <Label>商户id</Label>
                <StyledInput type="text" value={secrets.mch_id} onChange={e => setSecrets({ ...secrets, mch_id: e.target.value })} />
            </div>

            <div>
                <Label>商户证书序列号 </Label>
                <StyledInput type="text" value={secrets.mch_cert_serial} onChange={e => setSecrets({ ...secrets, mch_cert_serial: e.target.value })} />
            </div>

            <div>
                <Label>支付结果回调</Label>
                <StyledInput type="text" value={payCallback} onChange={e => setPayCallback(e.target.value)} />
            </div>

            <div>
                <Label>支付有效期(秒)</Label>
                <StyledInput type="number" min={0} value={payExpires} onChange={e => setPayExpires(e.target.value)} />
            </div>
        </Box>

        <Box gap={Gap}>
            <Title gap={Gap}>API设置</Title>
            <div>
                <Label>AppID</Label>
                <StyledInput type="text" value={secrets.app_id} onChange={e => setSecrets({ ...secrets, app_id: e.target.value })} />
            </div>
            <div>
                <Label>AppSecret</Label>
                <StyledInput type="text" value={secrets.app_secret} onChange={e => setSecrets({ ...secrets, app_secret: e.target.value })} />
            </div>
        </Box>

        <Box gap={Gap}>
            <Title gap={Gap}>增强安全设置</Title>
            <div>
                <Label>公钥ID</Label>
                <StyledInput type="text" value={secrets.pub_key_id} onChange={e => setSecrets({ ...secrets, pub_key_id: e.target.value })} />
            </div>
            <div>
                <Label>APIv3密码</Label>
                <StyledInput type="text" value={secrets.api_v3_pwd} onChange={e => setSecrets({ ...secrets, api_v3_pwd: e.target.value })} />
            </div>
            <div style={{ marginBottom: Gap.xm }} />
            <div>
                <Label>公钥</Label>
                <br />
                <StyledTextarea value={secrets.pub_key} onChange={e => setSecrets({ ...secrets, pub_key: e.target.value })} />
            </div>
            <div style={{ marginBottom: Gap.xm }} />
            <div>
                <Label>私钥</Label>
                <br />
                <StyledTextarea value={secrets.api_client_key} onChange={e => setSecrets({ ...secrets, api_client_key: e.target.value })} />
            </div>
        </Box>

        <Box gap={Gap}>
            <StyledButton onClick={saveChange}>应用</StyledButton>
        </Box>
    </div>
}

export default function WechatSettingsPanel(props) {
    return <StyledContainer>
        <SecretsPanel />
    </StyledContainer>
}
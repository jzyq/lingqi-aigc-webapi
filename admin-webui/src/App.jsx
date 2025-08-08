import { useState } from "react"
import { useTheme, ThemeProvider } from '@mui/material/styles';
import Tabs from "@mui/material/Tabs"
import Tab from "@mui/material/Tab"
import Stack from "@mui/material/Stack"
import Box from "@mui/material/Box"
import Subscription from "./ui/Subscription";
import Paper from "@mui/material/Paper";
import { ConditionContent } from "./component/container";
import { getLocalAuthToken, setLocalAuthToken, AuthProvider } from "./lib/Auth";
import Login from "./ui/Login"
import System from "./ui/System"


export default function App() {
    const theme = useTheme()
    const [pageIdx, setPageIdx] = useState(0)
    const [authToken, setAuthToken] = useState(getLocalAuthToken())

    const setToken = tk => {
        setLocalAuthToken(tk)
        setAuthToken(tk)
    }

    return (
        <ThemeProvider theme={theme}>
            <AuthProvider value={[authToken, setToken]}>
                <Box width={'100vw'} height={'100vh'}>

                    <ConditionContent show={authToken === null}>
                        <Login />
                    </ConditionContent>

                    <ConditionContent show={authToken !== null}>
                        <Stack height='stretch'>
                            <Paper variant="outlined">
                                <Tabs value={pageIdx} onChange={(e, v) => setPageIdx(v)}>
                                    <Tab label="首页设置" value={0} />
                                    <Tab label="用户管理" value={1} />
                                    <Tab label="订阅管理" value={2} />
                                    <Tab label="系统设置" value={3} />
                                </Tabs>
                            </Paper>
                            <Box width={"stretch"} height={"stretch"}>
                                <ConditionContent show={pageIdx === 0}>mainpage</ConditionContent>
                                <ConditionContent show={pageIdx === 1}>user</ConditionContent>
                                <ConditionContent show={pageIdx === 2}><Subscription /></ConditionContent>
                                <ConditionContent show={pageIdx === 3}><System /></ConditionContent>
                            </Box>
                        </Stack>
                    </ConditionContent>

                </Box>
            </AuthProvider>
        </ThemeProvider>
    )
}




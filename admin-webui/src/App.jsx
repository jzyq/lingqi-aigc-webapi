import styled from "@emotion/styled"
import { useState } from "react"
import Link from "./component/Link"
import System from "./ui/System"
import Theme from "./lib/Theme"
import { ThemeProvider } from "@emotion/react"
import Login from "./ui/Login"
import Router from "./lib/Router"

const AppContainer = styled.div`
  height: 100vh;
  width: 100vw;
  position: relative;
  display: flex;
  flex-direction: column;
`

const HeaderContainer = styled.header`
  height: 48px;
  z-index: 1;
  width: stretch;
  position: absolute;
  top: 0;
  background-color: ${props => props.theme.primary};
  display: flex;
  justify-content: space-between;
`

const MainContainer = styled.div`
  width: stretch;
  height: stretch;
  position: absolute;
  top: 48px;
`

const NavBar = styled.div`
  height: stretch;
  display: flex;
  align-items: center;
`

const routes = {
    "/login": <Login />,
    "/mainpage": <Main><h1>mainpage</h1></Main>,
    "/user": <Main><h1>user</h1></Main>,
    "/subscription": <Main><h1>subscription</h1></Main>,
    "/system": <Main><System /></Main>
}

function route(path) {
    path = path.replace("/aigc/admin", "")
    return routes[path]
}

function Main({ children }) {
    return <>
        <HeaderContainer>
            <NavBar>
                <Link href="/aigc/admin/mainpage">首页</Link>
                <Link href="/aigc/admin/user">用户</Link>
                <Link href="/aigc/admin/subscription">订阅</Link>
                <Link href="/aigc/admin/system">系统</Link>
            </NavBar>
        </HeaderContainer>

        <MainContainer>
            {children}
        </MainContainer>
    </>
}

export default function App() {
    const [path, setPath] = useState("/aigc/admin/mainpage")
    const content = route(path);

    return (
        <ThemeProvider theme={new Theme()}>
            <AppContainer>
                <Router value={[path, setPath]}>
                    {content}
                </Router>
            </AppContainer>
        </ThemeProvider>
    )
}




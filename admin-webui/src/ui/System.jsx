import styled from "@emotion/styled"
import { useState } from "react";
import WechatSettingsPanel from "./WechatSettings";

const MainContainer = styled.div`
    margin: 0;
    padding: 0;
    display: flex;
    position: relative;
    height: stretch;
    width: stretch;
`

const SectionSelector = styled.div`
    width: 160px;
    height: stretch;
    display: flex;
    flex-direction: column;
    background-color: ${props => props.theme.secondary};
`

const Content = styled.div`
    width: stretch;
    height: stretch;
    position: absolute;
    left: 160px;
`

const Tab = styled.div`
    width: stretch;
    height: 48px;
    align-content: center;
    text-align: center;
    color: white;
    :hover {
        background-color: ${props => props.theme.secnodaryLighten}
    }
`

const tabs = {
    'wechat': WechatSettingsPanel
}

export default function System(props) {

    const [currentTab, setCurrentTab] = useState('wechat')
    const ContentToRender = tabs[currentTab]

    return <MainContainer>
        <SectionSelector>
            <Tab>微信设置</Tab>
        </SectionSelector>
        <Content>
            <ContentToRender {...props} />
        </Content>
    </MainContainer>
}
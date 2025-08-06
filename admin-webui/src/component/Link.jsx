import styled from "@emotion/styled";
import Router from "../lib/Router";
import { useContext } from "react";

const A = styled.a`
    min-width: 64px;
    height: stretch;
    align-content: center;
    text-align: center;
    text-decoration: none;
    color: white;
    :hover {
        background-color: ${props => props.theme.primaryLighten};
    }
`

export default function Link(props) {

    const [path, navigateTo] = useContext(Router)

    const eventHandler = (event) => {
        event.preventDefault();
        window.history.pushState({}, '', props.href)
        navigateTo(props.href)
    }

    return <A href={props.href} onClick={eventHandler}>{props.children}</A>
}
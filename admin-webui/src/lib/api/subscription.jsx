import { useContext } from "react"
import AuthProvider from "../auth"
import { useState } from "react";
import { useEffect } from "react";

const SUBSCRIPTION_PLAN_URL = "/aigc/admin/api/subscription/plan"
const SUBSCRIPTION_PLAN_ENABLE_URL = pid => SUBSCRIPTION_PLAN_URL + `/${pid}/enable`
const SUBSCRIPTION_PLAN_DISABLE_URL = pid => SUBSCRIPTION_PLAN_URL + `/${pid}/disable`

async function getPlans(token, setToken) {
    const resp = await fetch(SUBSCRIPTION_PLAN_URL, {
        method: "GET",
        headers: {
            'authorization': `bearer ${token}`
        }
    });

    if (resp.status === 401) {
        setToken(null);
        return;
    }

    if (resp.status !== 200) {
        throw resp.statusText;
    }

    const data = await resp.json();

    if (data.code !== 0) {
        throw data.msg;
    }

    return data.data;
}

async function deletePlans(token, setToken, ids) {
    const resp = await fetch(SUBSCRIPTION_PLAN_URL, {
        method: "DELETE",
        headers: {
            'content-type': 'application/json',
            'authorization': `bearer ${token}`
        },
        body: JSON.stringify({ ids: ids })
    });

    if (resp.status === 401) {
        setToken(null);
        return;
    }

    if (resp.status !== 200) {
        throw resp.statusText;
    }

    const data = await resp.json();
    if (data.code != 0) {
        throw data.msg;
    }
}

async function addNewPlan(token, setToken, plan) {
    const resp = await fetch(SUBSCRIPTION_PLAN_URL, {
        method: "POST",
        headers: {
            'content-type': 'application/json',
            'authorization': `bearer ${token}`
        },
        body: JSON.stringify(plan)
    });

    if (resp.status === 401) {
        setToken(null);
        return;
    }

    if (resp.status !== 200) {
        throw resp.statusText;
    }

    const data = await resp.json();
    if (data.code != 0) {
        throw data.msg;
    }
}

async function enablePlan(token, setToken, pid, enable) {
    let url = ""
    if (enable) {
        url = SUBSCRIPTION_PLAN_ENABLE_URL(pid)
    } else {
        url = SUBSCRIPTION_PLAN_DISABLE_URL(pid)
    }

    const resp = await fetch(url, {
        method: "POST",
        headers: {
            'authorization': `bearer ${token}`
        }
    });

    if (resp.status === 401) {
        setToken(null);
        return;
    }

    if (resp.status !== 200) {
        throw resp.statusText;
    }

    const data = await resp.json();
    if (data.code != 0) {
        throw data.msg;
    }
}

export function useSubscriptionPlans() {
    const [token, setToken] = useContext(AuthProvider);
    const [plans, setPlans] = useState([]);
    const [needUpdate, setUpdate] = useState(0)

    useEffect(() => {
        getPlans(token, setToken).then(setPlans).catch(alert);
    }, [needUpdate])

    const adder = p => {
        addNewPlan(token, setToken, p);
        setUpdate(needUpdate + 1);
    };

    const deleter = ids => {
        deletePlans(token, setToken, ids);
        setUpdate(needUpdate + 1);
    }

    const changeState = (pid, enable) => {
        enablePlan(token, setToken, pid, enable)
        setUpdate(needUpdate + 1);
    }

    return [plans, adder, deleter, changeState];
}
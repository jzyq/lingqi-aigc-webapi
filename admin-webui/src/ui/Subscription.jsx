import Stack from "@mui/material/Stack";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useState } from "react";
import TableContainer from "@mui/material/TableContainer";
import Table from "@mui/material/Table";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import TableBody from "@mui/material/TableBody";
import Paper from "@mui/material/Paper";
import Button from "@mui/material/Button";
import ButtonGroup from "@mui/material/ButtonGroup";
import NewPlanDialog from "./NewPlanDialog";
import { ContentBox, SideBox } from "../component/container";
import { useSubscriptionPlans } from "../lib/api/subscription";


function AlignedTableCell(props) {
    return <TableCell align="center">{props.children}</TableCell>
}

function SubscriptionItem({ value, onDelete, onSetEnable }) {
    const typeNames = { subscription: "订阅" }
    const unitNames = { month: "月" }


    return <TableRow>
        <AlignedTableCell>{value.id}</AlignedTableCell>
        <AlignedTableCell>{typeNames[value.stype]}</AlignedTableCell>
        <AlignedTableCell>{value.price}</AlignedTableCell>
        <AlignedTableCell>{`${value.expires}${unitNames[value.unit]}`}</AlignedTableCell>
        <AlignedTableCell>{value.point}</AlignedTableCell>
        <AlignedTableCell>
            {value.enable ?
                <Button color="success" onClick={() => onSetEnable(value.id, false)}>已启用</Button> :
                <Button color="error" onClick={() => onSetEnable(value.id, true)}>已禁用</Button>}
        </AlignedTableCell>
        <AlignedTableCell>
            <ButtonGroup variant="contained">
                <Button color="error" onClick={() => onDelete(value.id)}>删除</Button>
            </ButtonGroup>

        </AlignedTableCell>
    </TableRow>
}

function SubscriptionPlans() {
    const [open, setOpen] = useState(false);
    const [plans, addNewPlan, deletePlans, changeState] = useSubscriptionPlans();

    const onDialogClose = v => {
        setOpen(false)
        if (v === null) {
            return;
        }
        addNewPlan(v);
    }

    return <>
        <TableContainer component={Paper} elevation={2}>
            <Table size="small">
                <TableHead>
                    <TableRow>
                        <AlignedTableCell>id</AlignedTableCell>
                        <AlignedTableCell>类型</AlignedTableCell>
                        <AlignedTableCell>订价</AlignedTableCell>
                        <AlignedTableCell>有效期</AlignedTableCell>
                        <AlignedTableCell>施法点</AlignedTableCell>
                        <AlignedTableCell>状态</AlignedTableCell>
                        <AlignedTableCell>
                            <Button
                                variant="contained"
                                color="success"
                                onClick={() => setOpen(true)}
                            >
                                新订阅
                            </Button>
                        </AlignedTableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {plans.map(p => <SubscriptionItem
                        key={p.id}
                        value={p}
                        onDelete={id => deletePlans([id])}
                        onSetEnable={changeState} />)}
                </TableBody>
            </Table>
        </TableContainer>
        <NewPlanDialog open={open} onClose={onDialogClose} />
    </>
}

export default function Subscription() {
    const [currentTab, setCurrentTab] = useState(0)

    return <Stack direction="row" height={'100%'}>
        <SideBox>
            <Tabs
                value={currentTab}
                onChange={(e, v) => { setCurrentTab(v) }}
                orientation="vertical"
            >
                <Tab value={0} label="订阅方案" />
            </Tabs>
        </SideBox>
        <ContentBox>
            <SubscriptionPlans />
        </ContentBox>
    </Stack>
}
import { useState } from "react";
import Dialog from "@mui/material/Dialog";
import Typography from "@mui/material/Typography";
import Select from "@mui/material/Select";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Box from "@mui/material/Box";
import ButtonGroup from "@mui/material/ButtonGroup";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";


const TYPE_SUBSCRIPTION = "subscription";
const UNIT_MONTH = "month";


function Header() {
    return <Box>
        <Typography variant="h6">新增订阅方案</Typography>
    </Box>
}

function InputBox({ value, onChange }) {

    const validateExpires = v => {
        if (v >= 1) {
            onChange({ ...value, expires: v })
        }
    }

    const validatePrice = v => {
        if (v >= 1) {
            onChange({ ...value, price: v })
        }
    }

    const validatePoint = v => {
        if (v >= 1) {
            onChange({ ...value, point: v })
        }
    }


    return <Stack spacing={2} py={1}>
        <Stack direction="row" spacing={1} justifyContent={"space-between"}>
            <FormControl fullWidth size="small">
                <InputLabel id="label_select_plan_type">类型</InputLabel>
                <Select
                    id="ipt_plan_type"
                    labelId="label_select_plan_type"
                    label="类型"
                    value={value.stype}
                    onChange={e => onChange({ ...value, type: e.target.value })}
                >
                    <MenuItem value={TYPE_SUBSCRIPTION}>包月</MenuItem>
                </Select>
            </FormControl>
            <TextField
                size="small"
                label="时长"
                type="number"
                fullWidth
                id="ipt_plan_expires"
                value={value.expires}
                onChange={e => validateExpires(e.target.value)}
            />
        </Stack>
        <Stack direction="row" spacing={1}>
            <TextField
                size="small"
                label="价格(分)"
                type="number"
                fullWidth
                id="ipt_plan_price"
                value={value.price}
                onChange={e => validatePrice(e.target.value)}
            />
            <TextField
                size="small"
                label="点数"
                type="number"
                fullWidth
                id="ipt_plane_point"
                value={value.point}
                onChange={e => validatePoint(e.target.value)}
            />
        </Stack>
    </Stack>

}

export default function NewPlanDialog({ open, onClose }) {

    const [value, setValue] = useState({
        stype: TYPE_SUBSCRIPTION,
        expires: 1,
        price: 1,
        unit: UNIT_MONTH,
        point: 1,
        enable: false
    });

    return <Dialog open={open}>
        <Paper sx={{ px: 2, py: 1 }}>
            <Stack spacing={1.5} divider={<Divider flexItem />}>
                <Header />
                <InputBox value={value} onChange={setValue} />

                <Stack direction="row-reverse">
                    <ButtonGroup variant="contained">
                        <Button color="primary" onClick={() => onClose(null)}>取消</Button>
                        <Button color="success" onClick={() => onClose(value)}>好</Button>
                    </ButtonGroup>
                </Stack>

            </Stack>
        </Paper>
    </Dialog>
}

import Box from "@mui/material/Box"
import Paper from "@mui/material/Paper"

export function ContentBox(props) {
    return <Box sx={{
        px: 3,
        py: 2,
        width: 'stretch'
    }}>
        {props.children}
    </Box>
}

export function SideBox(props) {
    return <Paper variant="outlined" sx={{ width: 128 }}>
        {props.children}
    </Paper>
}

export function ConditionContent({ show, children }) {
    if (show) {
        return <>{children}</>
    } else {
        return null
    }
}
import { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";
import AppRouter from "./router";
import useUIStore from "./store/uiStore";

export default function App() {
    const theme = useUIStore((state) => state.theme);

    useEffect(() => {
        document.documentElement.dataset.theme = theme;
    }, [theme]);

    return (
        <BrowserRouter>
            <AppRouter />
        </BrowserRouter>
    );
}

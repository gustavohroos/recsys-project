import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import Onboarding from "../pages/Onboarding";

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/onboarding" element={<Onboarding />} />
      </Routes>
    </BrowserRouter>
  );
}

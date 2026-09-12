import { BrowserRouter, Route, Routes } from "react-router"

import AppShell from "@/components/AppShell"
import Operations from "@/pages/Operations"
import RunDetails from "@/pages/RunDetails"
import { SimulationProvider } from "@/context/SimulationContext"

function App() {
  return (
    <SimulationProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<Operations />} />
            <Route
              path="/runs/:shipmentId/:runId"
              element={<RunDetails />}
            />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </SimulationProvider>
    
  )
}

export default App